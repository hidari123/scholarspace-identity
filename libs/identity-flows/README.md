# scholarspace-identity-flows

> 流程引擎 —— **Stage + Policy 编排**，借鉴 authentik 的架构思想。

---

## 这是什么

登录注册不是一串硬编码的 `if-else`，而是**可配置的步骤序列**。

```
Flow(
    name="signup_wechat",
    stages=(SignUpOAuthStage(), BindEmailStage(), CreateUserStage()),
    policies=(EmailRequiredPolicy(),),
)
```

---

## 三个概念

| 概念 | 是什么 | 例子 |
|---|---|---|
| **Stage** | 流程中的一步 | 收集邮箱 / 设置密码 / OAuth 回调 / 绑定邮箱 / 创建用户 |
| **Policy** | 一条业务策略 | 邮箱必绑 / 手机号必绑 |
| **Flow** | Stage 序列 + Policy 组合 | `signup_wechat` |

---

## 执行逻辑

```
1. 依次跑每个 Stage
2. 每跑完一个 Stage，评估 Policy
   ├─ 要求某个 Stage → 跳到那个 Stage
   ├─ 拒绝            → 流程终止（DENIED）
   └─ 继续            → 下一个 Stage
3. 全部跑完 → COMPLETED
```

**短路语义**：任一 Policy 要求 Stage 或拒绝，就不再评估后面的 —— Policy 顺序即优先级。

**防死循环**：同一个 Stage 不会重复执行（`executed` 集合）。

---

## 核心场景：微信注册必须补邮箱

微信开放平台的 `sns/userinfo` 接口**不返回邮箱**。

如果直接放行，平台上就会有一批「既没有邮箱也没有手机号」的用户 ——
无法联系、无法找回密码。

所以微信流程强制走 `BindEmailStage`：

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

---

## FlowStatus

| 状态 | 含义 | HTTP |
|---|---|---|
| `COMPLETED` | 全部完成 | 200 |
| `PENDING` | 需要用户补充信息（挂起）| 202 |
| `FAILED` | 失败 | 400 |
| `DENIED` | 被策略拒绝 | 403 |

---

## 用法

```python
from identity_flows import run_signup

result = run_signup("email", {"email": "a@b.com", "password": "secret123"})

if result.ok:
    print(result.user.user_id)
    print(result.events)   # [UserRegistered(...)]
elif result.status == FlowStatus.PENDING:
    print("需要用户补充信息")
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
- [identity-core](../identity-core/README.md) —— 领域模型与 Policy
