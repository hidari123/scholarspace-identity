# scholarspace-identity-providers

> 各登录方式的适配 —— 邮箱密码 / 微信 / Google / GitHub / 短信。

---

## 这是什么

把「怎么跟第三方对话」的细节封装起来，让上层（流程引擎）只关心
「这个用户是谁」。

```
┌─────────────────────────────────────────────────┐
│  identity-flows                                   │
│    Flow(stages=[SignUpOAuthStage(), ...])        │
└──────────────────┬──────────────────────────────┘
                   │ 只看 ProviderProfile
┌──────────────────▼──────────────────────────────┐
│  identity-providers                               │
│    WechatProvider / GoogleProvider / ...         │
└──────────────────┬──────────────────────────────┘
                   │ HTTP
┌──────────────────▼──────────────────────────────┐
│  微信开放平台 / Google / GitHub / 邮件服务         │
└─────────────────────────────────────────────────┘
```

---

## Provider 分类

| 类型 | Provider | 邮箱 | 备注 |
|---|---|---|---|
| **OAuth2** | `WechatProvider` | ❌ **没有** | 开放平台网站应用，`snsapi_login` |
| **OAuth2** | `GoogleProvider` | ✅ 有 | OIDC，Google 保证已验证 |
| **OAuth2** | `GitHubProvider` | ⚠️ 可能有 | 主邮箱可能**未验证** |
| **凭证** | `EmailPasswordProvider` | ✅ 有 | 密码哈希校验 |

---

## 微信：两个必须修的安全问题

参考 `scholar-club` 旧实现时发现的：

### ① state 未校验 → CSRF 漏洞

**旧实现**：前端生成 `state` 塞进 URL，后端**从不校验**。
攻击者可以构造一个带自己 code 的链接发给受害者，受害者登录后
**登录到了攻击者的账号**。

**本实现**：

```python
provider = WechatProvider(config=wechat_config)

state = provider.generate_state()      # 服务端生成 + HMAC 签名
url = provider.build_authorize_url(state)

# 回调时
provider.verify_state(state, expected_state=session_state)  # 强制校验
```

state 格式：`<随机串>.<过期时间戳>.<HMAC签名>`

校验三件事：
1. **签名匹配** —— 客户端伪造不出来
2. **未过期** —— 防重放
3. **与会话中一致** —— 防跨会话重放

⚠️ **state 必须由服务端生成** —— 客户端生成的服务端无法校验。

### ② JWT 密钥硬编码兜底 → 上线即泄露

**旧实现**：`JWT_SECRET || 'your-jwt-secret-key'`
→ 忘记配置环境变量时，系统用这个公开字符串签名，生产环境的 token
谁都能伪造。

**本实现**：`WechatConfig.__post_init__` 里**没有兜底**：

```python
if not self.secret:
    raise ValueError("微信 secret 未配置")   # 缺失即启动失败
```

---

## GitHub 的邮箱坑

```python
# GET /user
{"id": 123, "login": "octocat", "email": null}   # ⚠️ 邮箱可能为 null

# GET /user/emails
[
  {"email": "old@example.com", "primary": false, "verified": true},
  {"email": "main@example.com", "primary": true,  "verified": false},  # ⚠️ 主邮箱未验证
]
```

**GitHub 登录的用户也要走「邮箱必绑」策略** —— 拿到未验证的邮箱时，
要求用户再验证一次。

`_pick_email()` 的优先级：
1. primary **且** verified
2. 任意 verified
3. primary（可能未验证）
4. `user_data.email`（可能为 null）

---

## 密码处理

```python
from identity_providers import Argon2Hasher, BcryptHasher, EmailPasswordProvider

provider = EmailPasswordProvider(hasher=Argon2Hasher())
password_hash = provider.hash_password("Str0ngPassword!")   # 注册时
provider.verify_password("Str0ngPassword!", password_hash)  # 登录时
```

**原则**：

| 规则 | 原因 |
|---|---|
| 只存哈希 | 泄露数据库不等于泄露密码 |
| argon2 / bcrypt，**不用 MD5/SHA1** | 需要自带盐 + 可调成本 |
| 哈希器**端口化**（`PasswordHasher` Protocol）| 换算法不动调用方 |
| 强度规则**可解释** | 只说「太弱」用户不知道怎么改 |

**强度规则**：≥10 位 + 至少一个数字 + 至少一个字母。

---

## 验证码

```python
from identity_providers import generate_verification_code

code = generate_verification_code()   # 6 位数字
```

⚠️ 用 `secrets` 而非 `random` —— 验证码可预测就是漏洞。

---

## 用法

```python
from identity_providers import WechatConfig, WechatProvider

provider = WechatProvider(
    config=WechatConfig(
        appid=appid,
        secret=secret,
        redirect_uri="https://scholar.example.com/api/identity/wechat/callback",
        state_secret=state_secret,
    )
)

# 1. 生成授权 URL（前端拿去做二维码）
state = provider.generate_state()
url = provider.build_authorize_url(state)

# 2. 回调时换档案
profile = await provider.exchange_code(code, state=state)
# → OAuthProfile(provider=WECHAT, provider_user_id=openid, email=None, ...)
```

---

## 质量门禁

```bash
uv venv --python 3.13
uv pip install -e ".[dev]" --no-deps
uv pip install pytest pytest-asyncio ruff mypy httpx bcrypt argon2-cffi

.venv/Scripts/ruff.exe check src/ tests/
.venv/Scripts/mypy.exe src/
.venv/Scripts/python.exe -m pytest tests/ -q
```

---

## 相关

- [scholarspace-identity](../../README.md) —— 整个仓
- [identity-core](../identity-core/README.md) —— 领域模型
- [identity-flows](../identity-flows/README.md) —— 流程引擎
