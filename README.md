# scholarspace-identity

> 登录注册服务 —— **邮箱必绑**，支持 邮箱 / 微信 / Google / GitHub / 手机号。
>
> 可复用到任何项目：装 `scholarspace-identity-core` 就能用领域模型与策略。

---

## 为什么独立成仓

用户明确要求：**「登陆注册这些我想单独拿出来做一个独立的 git 仓库，可以复用到别的上面」**

登录注册是**用户直接感知**的能力，也是最容易被复用的资产。

**旧系统的反面教材**（`scholar-club-backend`）：

```
routers/login_email_router.py     1720 行 —— 一个文件塞了所有登录方式
models/account_model.py            ACCOUNT 表把身份和业务混装：
    ACCOUNT_ID, UID, GOOGLE_ID, WECHAT_ID, ...       身份
    MASTODON_ID, MASTODON_PASSWORD,                  社区账号
    LITELLM_PAY_KEY, LITELLM_PAY_BUDGET_ID, ...      计费密钥
    LIFESTUDIO_USER_ID, LIFESTUDIO_USER_APIKEY, ...  第三方服务
```

**后果**：这个模块没法复用到任何别的项目 —— 因为它带着一堆跟身份无关的业务字段。

---

## 目录结构

```
scholarspace-identity/
├── libs/
│   ├── identity-core/           ⭐ 纯领域，零运行时依赖
│   │   ├── entities.py          User / Identity / Credential / EmailAddress / PhoneNumber
│   │   ├── policy.py            Policy 机制（借鉴 authentik）
│   │   └── events.py            领域事件（解耦下游）
│   │
│   ├── identity-flows/          ⭐ 流程引擎（Stage + Policy）
│   │   ├── engine.py            Stage 协议 / Flow 定义 / 执行算法
│   │   ├── flows.py             各注册方式的具体流程
│   │   └── runner.py            对外执行入口
│   │
│   ├── identity-providers/      各登录方式的适配
│   │   ├── base.py              Provider 统一抽象
│   │   ├── oauth2/
│   │   │   ├── state.py         ⭐ 共享的防 CSRF state 机制
│   │   │   ├── wechat.py        微信开放平台网站应用
│   │   │   └── standard.py      Google / GitHub
│   │   └── password/
│   │       └── email_password.py  argon2 / bcrypt + 验证码
│   │
│   └── identity-http/           HTTP 接口层
│       ├── ports.py             存储端口（Protocol）
│       ├── schemas.py           请求/响应模型
│       ├── app.py               FastAPI 应用工厂
│       ├── routers/auth.py      认证路由
│       └── storage/in_memory.py 内存实现（开发/测试）
│
└── ui/                          登录/注册前端组件（待建）
```

---

## 状态

| 包 | 测试 | 门禁 |
|---|---|---|
| `identity-core` | 39 | ✅ 全绿 |
| `identity-flows` | 23 | ✅ 全绿 |
| `identity-providers` | 55 | ✅ 全绿 |
| `identity-http` | 22 | ✅ 全绿 |
| **合计** | **139** | |

每包的门禁：`ruff check` + `ruff format --check` + `mypy src/` + `pytest`

---

## 三个核心设计

### 1. 身份与业务彻底分离

```python
from identity_core import User, EmailAddress

user = User.create(email=EmailAddress("a@b.com"))
```

**`User` 里没有任何业务字段** —— 没有余额、没有配额、没有社区密码。

旧系统的 `ACCOUNT` 表把这些全塞进去，结果就是这个模块没法复用。

### 2. 事件解耦

```python
from identity_core import UserRegistered

event = UserRegistered(user_id=user.user_id, email="a@b.com", providers=("wechat",))
```

identity **只发事件**，不知道下游有谁：

```python
# billing 订阅
async def on_user_registered(event: UserRegistered) -> None:
    await billing.create_account(event.user_id)

# community 订阅
async def on_user_registered(event: UserRegistered) -> None:
    await community.create_account(event.user_id)
```

**identity 永远不需要知道 billing 的存在。**

### 3. 邮箱必绑 = Policy，不是硬编码

```python
from identity_core import EmailRequiredPolicy, evaluate_policies

decision = evaluate_policies([EmailRequiredPolicy()], user)
# → REQUIRE_STAGE(email_verification)
```

「邮箱必绑」是**业务策略**，不同租户要求可能不同。写成 Policy 后：
- 规则集中可测
- 换租户只换 Policy 组合，不改流程代码
- 策略可组合、可排序

---

## 为什么微信必须补邮箱

微信开放平台（网站应用，`snsapi_login` scope）的 `sns/userinfo` 接口**不返回邮箱**。

如果直接放行，平台上就会有一批「既没有邮箱也没有手机号」的用户 ——
**无法联系、无法找回密码**。

所以微信注册流程强制走 `BindEmailStage`：

```python
_SIGNUP_WECHAT = Flow(
    name="signup_wechat",
    stages=(
        SignUpOAuthStage(),   # 微信授权回调 → 拿到 openid
        BindEmailStage(),     # ⚠️ 强制补邮箱
        CreateUserStage(),    # 建用户
    ),
    policies=(EmailRequiredPolicy(),),
)
```

**各方式的邮箱处理：**

| 方式 | 有邮箱吗 | 处理 |
|---|---|---|
| 邮箱+密码 | 有 | 验证后完成 |
| Google | 有（`email` scope）| 验证即可 |
| GitHub | 有（`user:email` scope）| 无邮箱则要求补 |
| **微信** | **没有** | ⚠️ **强制补邮箱并验证** |

---

## 身份标识：用 openid 不用昵称

```python
identity = Identity(provider=ProviderType.WECHAT, provider_user_id="oABC123")
```

⚠️ **昵称会变，openid 不会** —— 用昵称做身份标识，用户改个昵称就登不上了。

---

## 借鉴 authentik 的部分

| authentik | 我们的实现 | 借鉴程度 |
|---|---|---|
| Stage 流程 | `identity-flows/engine.py` | ✅ 架构思想 |
| Policy | `identity-core/policy.py` | ✅ 架构思想 |
| Event + 钩子 | `identity-core/events.py` | ✅ 架构思想 |
| 完整 OAuth2/OIDC IdP | — | ❌ 不做（工作量 ×3）|
| Source / Provider 分离 | — | ❌ 不做（我们不存 LDAP）|
| Outpost | — | ❌ 不做（provider 都是纯 HTTP 调用）|

**只借鉴架构思想，实现完全自研。**

---

## 微信登录的安全要点

参考 `scholar-club` 已有的实现，但**修掉两个问题**：

| # | 问题 | scholarclaw 的做法 | 本仓的做法 |
|---|---|---|---|
| 1 | **state 校验缺失** | 前端生成 state 但后端从不校验 → **CSRF 漏洞** | 后端生成并签名，校验签名 + 有效期 + 未使用 |
| 2 | **JWT 密钥硬编码兜底** | `JWT_SECRET \|\| 'your-jwt-secret-key'` → **上线即泄露** | 无兜底，缺失即启动失败 |

另外：
- 微信 `access_token` **不写日志**（scholarclaw 打了前 20 字符）
- `redirect_uri` **按环境配置**，不硬编码
- AppID **只存服务端**，前端不硬编码（scholarclaw 有默认值兜底）

---

## 质量门禁

每个包独立：

```bash
cd libs/identity-core
uv venv --python 3.13
uv pip install -e ".[dev]" --no-deps
uv pip install pytest pytest-asyncio ruff mypy

.venv/Scripts/ruff.exe check src/ tests/
.venv/Scripts/ruff.exe format --check src/ tests/
.venv/Scripts/mypy.exe src/
.venv/Scripts/python.exe -m pytest tests/ -q
```

当前：**62 tests passed**（core 39 + flows 23）

---

## 相关

- [ADR-0016](../../scholarspace/docs/adr/0016-repo-layout-and-identity.md) —— 为什么独立成仓
- [12-独立仓与共享UI设计](../../scholarspace/docs/12-独立仓与共享UI设计.md)
- [脚手架插件开发](../../scholarspace/cli/docs/plugin.md)
