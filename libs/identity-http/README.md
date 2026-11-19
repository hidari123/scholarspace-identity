# scholarspace-identity-http

> HTTP 接口层 —— FastAPI 路由 + 存储。

---

## 这是什么

最后一层。**很薄** —— 只做三件事：

```
① 解析请求（Pydantic 校验）
② 调 application / flows 层
③ 包装响应
```

业务逻辑在 `identity-flows` / `identity-providers`，领域规则在 `identity-core`。

---

## 目录

```
src/identity_http/
├── ports.py       存储端口（Protocol）—— 定义在应用层
├── schemas.py     请求/响应模型（Pydantic v2）
├── app.py         FastAPI 应用工厂
├── routers/
│   └── auth.py    认证路由
└── storage/
    └── in_memory.py   内存实现（开发/测试用）
```

---

## 端点

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/identity/signup` | 注册 |
| POST | `/api/identity/login` | 登录 |
| POST | `/api/identity/verification-code` | 发验证码 |
| POST | `/api/identity/verification-code/verify` | 校验验证码 |
| GET | `/api/identity/wechat/authorize` | 微信扫码授权 URL |
| POST | `/api/identity/wechat/callback` | 微信回调 |
| GET | `/health` | 健康检查 |

---

## 端口在应用层，实现在基础设施层

```python
# ports.py —— 只有接口，没有实现
class UserRepository(Protocol):
    async def get_by_email(self, email: str) -> User | None: ...
    async def get_by_identity(self, provider, provider_user_id) -> User | None: ...
```

```python
# routers/auth.py —— 路由只依赖接口
async def signup(payload: SignupRequest, users: UserRepoDep) -> SignupResponse:
    ...
```

```python
# storage/in_memory.py —— 实现
class InMemoryUserRepository:
    ...
```

**好处**：
- 路由代码换数据库**一行都不用改**
- 测试塞内存实现，不用起数据库
- 领域层不沾 SQLAlchemy

---

## 几个刻意的设计决定

### ① 用户不存在与密码错误返回同一个错误

```python
# ❌ 区分两者会泄露「这个邮箱注册过」
if user is None:
    raise HTTPException(400, "用户不存在")
raise HTTPException(400, "密码错误")

# ✅ 统一
raise HTTPException(401, {"code": "identity.invalid_credentials", "message": "邮箱或密码错误"})
```

### ② 发验证码的响应里**没有**验证码

```python
return {"status": "sent"}   # ⚠️ 绝不能把 code 返回给客户端
```

否则等于绕过邮箱验证 —— 攻击者给自己发个码就知道码是什么。

### ③ 验证码一次性 + 按用途隔离

```python
await codes.verify_and_consume(target, code, purpose)
#                       ↑ 校验通过后立即删除 —— 同一个码不能用第二次
```

`purpose` 参与 key —— 「注册用码」和「改密码用码」即使数字相同也不能混用。

### ④ 微信没配置就 503，不静默降级

```python
if missing:
    raise HTTPException(503, {"code": "identity.not_configured", ...})
```

⚠️ 旧实现里有 `JWT_SECRET || 'your-jwt-secret-key'` 这种兜底 ——
忘记配置时系统用公开字符串照常工作，上线即泄露。

### ⑤ 流程状态 → HTTP 状态码的映射

| FlowStatus | HTTP | 理由 |
|---|---|---|
| `COMPLETED` | 200 | 成功 |
| `PENDING` | **202** | 需要用户补充信息，**不是错误** |
| `FAILED` | 400 | 失败 |
| `DENIED` | 403 | 策略拒绝 |

---

## 微信配置

从环境变量读，**没有默认值**：

```
WECHAT_APPID
WECHAT_SECRET
WECHAT_REDIRECT_URI
IDENTITY_STATE_SECRET     # ⚠️ state 签名密钥 —— 没有它就没有 CSRF 防护
```

---

## 跑起来

```bash
uv venv --python 3.13
uv pip install -e ".[dev]" --no-deps
uv pip install pytest pytest-asyncio httpx fastapi "pydantic[email]" bcrypt ruff mypy

.venv/Scripts/ruff.exe check src/ tests/
.venv/Scripts/mypy.exe src/
.venv/Scripts/python.exe -m pytest tests/ -q
```

启动：

```bash
.venv/Scripts/python.exe -m uvicorn identity_http.app:create_app --factory --reload
```

---

## 相关

- [scholarspace-identity](../../README.md) —— 整个仓
- [identity-core](../identity-core/README.md) —— 领域模型
- [identity-flows](../identity-flows/README.md) —— 流程引擎
- [identity-providers](../identity-providers/README.md) —— 登录方式适配
