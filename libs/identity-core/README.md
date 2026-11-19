# scholarspace-identity-core

> 身份领域核心 —— **纯领域，零运行时依赖**。

---

## 这是什么

`scholarspace-identity` 仓的领域层。装它**不拖进 FastAPI / SQLAlchemy / 任何运行时依赖**。

这是本仓能被复用到任何项目的前提 —— 别的项目想用「邮箱必绑 + 多登录方式」的逻辑，
装这个包就够了。

---

## 提供什么

| 能力 | 内容 |
|---|---|
| **领域模型** | `User` `Identity` `Credential` `EmailAddress` `PhoneNumber` |
| **登录方式** | `ProviderType` —— 邮箱密码 / 微信 / Google / GitHub / 短信 |
| **策略机制** | `Policy` `PolicyDecision` `EmailRequiredPolicy` `PhoneRequiredPolicy` |
| **领域事件** | `UserRegistered` `UserEmailBound` `UserLoggedIn` `IdentityBound` |

---

## 核心设计：身份与业务彻底分离

```python
from identity_core import User, EmailAddress, ProviderType

user = User.create(email=EmailAddress("a@b.com").mark_verified())
user = user.with_identity(Identity(provider=ProviderType.WECHAT, provider_user_id="openid-123"))
```

**`User` 里没有任何业务字段** —— 没有余额、没有配额、没有社区密码。

这是旧系统 `ACCOUNT` 表的教训：

```python
# ❌ 旧系统 —— 身份与业务混装
class AccountModel(Base):
    ACCOUNT_ID, UID, GOOGLE_ID, WECHAT_ID, ...
    LITELLM_PAY_KEY, LITELLM_BONUS_KEY,      # ← 计费密钥
    MASTODON_ID, MASTODON_PASSWORD,          # ← 社区账号
    LIFESTUDIO_USER_ID, LIFESTUDIO_USER_APIKEY,  # ← 第三方服务
```

**结果**：identity 想复用到别的项目，这些字段全得带着走。

---

## 事件解耦

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

---

## 邮箱必绑（Policy 而非硬编码）

```python
from identity_core import EmailRequiredPolicy, evaluate_policies

decision = evaluate_policies([EmailRequiredPolicy()], user)
# → REQUIRE_STAGE(email_verification)
```

「邮箱必绑」是**业务策略**，不同租户要求不同 —— 写成 Policy 后：
- 规则集中可测
- 换租户只换 Policy 组合，不改流程代码
- 策略可组合、可排序（短路语义：任一策略要求 stage 就停）

---

## 微信注册的特殊处理

微信**不返回邮箱** —— 所以微信注册必须让用户补邮箱。

```python
from identity_core import ProviderType

# ⚠️ 用 openid 而不是昵称 —— 昵称会变，openid 不会
identity = Identity(provider=ProviderType.WECHAT, provider_user_id="oABC123")
```

---

## 质量门禁

```bash
uv venv --python 3.13
uv pip install -e ".[dev]" --no-deps
uv pip install pytest pytest-asyncio ruff mypy

.venv/Scripts/ruff.exe check src/ tests/
.venv/Scripts/mypy.exe src/
.venv/Scripts/python.exe -m pytest tests/ -q
```

---

## 相关

- [scholarspace-identity](../../README.md) —— 整个仓
- [ADR-0016](../../../scholarspace/docs/adr/0016-repo-layout-and-identity.md) —— 为什么独立
