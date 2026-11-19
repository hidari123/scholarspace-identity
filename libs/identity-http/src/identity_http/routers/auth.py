"""认证路由 —— 注册 / 登录 / 验证码。

⚠️ 这一层**很薄** —— 只做三件事：
    ① 解析请求（Pydantic 校验）
    ② 调 application 层
    ③ 包装响应

业务逻辑在 flows / providers 里，领域规则在 core 里。
"""

from __future__ import annotations

import os
from functools import cache
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from identity_core.entities import Credential, CredentialType, User
from identity_flows import FlowStatus, run_signup
from identity_providers import (
    BcryptHasher,
    WechatConfig,
    WechatProvider,
    generate_verification_code,
)

from identity_http.schemas import (
    EmailCodeRequest,
    LoginRequest,
    LoginResponse,
    SignupRequest,
    SignupResponse,
    UserResponse,
    VerifyCodeRequest,
    WechatAuthorizeResponse,
    WechatCallbackRequest,
)
from identity_http.storage.in_memory import (
    InMemoryCredentialRepository,
    InMemoryUserRepository,
    InMemoryVerificationCodeRepository,
)

__all__ = [
    "get_credential_repository",
    "get_user_repository",
    "get_verification_repository",
    "router",
]

router = APIRouter(prefix="/api/identity", tags=["identity"])


# ══════════════════════════════════════════════════════════
# 依赖注入
#
# ⚠️ 默认是内存实现 —— 生产环境覆盖这些依赖换成 PostgreSQL 实现。
#    这就是「端口在应用层，实现在基础设施层」的价值：
#    路由代码一行都不用改。
# ══════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════
# 依赖注入
#
# ⚠️ 默认是内存实现 —— 生产环境覆盖这些依赖换成 PostgreSQL 实现。
#    这就是「端口在应用层，实现在基础设施层」的价值：
#    路由代码一行都不用改。
#
# ⚠️ 用模块级单例而不是 global 语句 ——
#    global 会让并发场景下的初始化有竞态，也让测试难以隔离。
#    测试通过 dependency_overrides 覆盖，不受这里影响。
# ══════════════════════════════════════════════════════════


@cache
def get_user_repository() -> InMemoryUserRepository:
    """用户仓储依赖。

    ⚠️ 用 functools.cache 做单例 —— 比 global 干净，
       也不会有并发初始化的竞态。
    """
    return InMemoryUserRepository()


@cache
def get_credential_repository() -> InMemoryCredentialRepository:
    """凭证仓储依赖。"""
    return InMemoryCredentialRepository()


@cache
def get_verification_repository() -> InMemoryVerificationCodeRepository:
    """验证码仓储依赖。"""
    return InMemoryVerificationCodeRepository()


UserRepoDep = Annotated[Any, Depends(get_user_repository)]
CredentialRepoDep = Annotated[Any, Depends(get_credential_repository)]
CodeRepoDep = Annotated[Any, Depends(get_verification_repository)]


# ══════════════════════════════════════════════════════════
# 辅助
# ══════════════════════════════════════════════════════════


def _to_response(user: User) -> UserResponse:
    """领域对象 → 响应模型。"""
    return UserResponse(
        user_id=user.user_id,
        email=user.email.value if user.email else None,
        email_verified=user.has_verified_email,
        phone=user.phone.value if user.phone else None,
        phone_verified=user.phone is not None and user.phone.verified,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        providers=[provider.value for provider in user.providers],
        created_at=user.created_at.isoformat(),
    )


def _raise_for_status(flow_status: FlowStatus, reason: str | None) -> None:
    """把流程状态翻译成 HTTP 状态码。

    ⚠️ 映射原则：
        COMPLETED → 200
        PENDING   → 202（需要用户补充信息，不是错误）
        FAILED    → 400
        DENIED    → 403
    """
    if flow_status is FlowStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail={"code": "identity.pending", "message": reason or "需要补充信息"},
        )
    if flow_status is FlowStatus.DENIED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "identity.denied", "message": reason or "策略拒绝"},
        )
    if flow_status is FlowStatus.FAILED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "identity.failed", "message": reason or "注册失败"},
        )


# ══════════════════════════════════════════════════════════
# 注册
# ══════════════════════════════════════════════════════════


@router.post("/signup", response_model=SignupResponse)
async def signup(
    payload: SignupRequest,
    users: UserRepoDep,
    credentials: CredentialRepoDep,
) -> SignupResponse:
    """注册。

    ⚠️ 邮箱已被占用时返回 409 —— 这是最常见的冲突。
    """
    method = payload.method.strip().lower()

    # 邮箱注册要先查重
    if method == "email" and payload.email and await users.exists_by_email(payload.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "identity.email_taken", "message": "该邮箱已被注册"},
        )

    data: dict[str, Any] = {}
    if payload.email:
        data["email"] = payload.email
    if payload.password:
        data["password"] = payload.password
    if payload.phone:
        data["phone"] = payload.phone
    if payload.display_name:
        data["display_name"] = payload.display_name

    result = run_signup(method, data)
    _raise_for_status(result.status, result.error)

    if result.user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "identity.failed", "message": "注册未产出用户"},
        )

    # 落库
    await users.save(result.user)

    # ⚠️ 邮箱注册要存密码凭证 —— 否则用户注册完却永远登不进来。
    #    第三方登录（微信/Google/GitHub）没有密码，不存。
    if method == "email" and payload.password:
        await _store_password_credential(
            credentials,
            result.user.user_id,
            payload.password,
        )

    return SignupResponse(
        status=result.status.value,
        user=_to_response(result.user),
        next_step=None,
        reason=result.error,
    )


async def _store_password_credential(
    credentials: Any,
    user_id: UUID,
    password: str,
) -> None:
    """存密码凭证（哈希后存）。

    ⚠️ 只存哈希 —— 明文密码绝不入库。
    """
    provider = BcryptHasher()
    credential = Credential(
        user_id=user_id,
        credential_type=CredentialType.PASSWORD,
        secret_hash=provider.hash(password),
    )
    await credentials.save(credential)


# ══════════════════════════════════════════════════════════
# 登录
# ══════════════════════════════════════════════════════════


@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    users: UserRepoDep,
    credentials: CredentialRepoDep,
) -> LoginResponse:
    """登录。

    ⚠️ 失败时**统一**返回「邮箱或密码错误」——
       区分「用户不存在」与「密码错误」会泄露用户是否存在。
    """
    method = payload.method.strip().lower()

    if method != "email" or not payload.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "identity.unsupported_method", "message": "暂不支持的登录方式"},
        )

    user = await users.get_by_email(payload.email)
    if user is None or not payload.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "identity.invalid_credentials", "message": "邮箱或密码错误"},
        )

    credential = await credentials.get_by_user_and_type(user.user_id, CredentialType.PASSWORD)
    if credential is None or not credential.secret_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "identity.invalid_credentials", "message": "邮箱或密码错误"},
        )

    # ⚠️ bcrypt 的 cost 可能与当前配置不同 —— 用存的哈希自身的参数校验
    if not BcryptHasher().verify(payload.password, credential.secret_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "identity.invalid_credentials", "message": "邮箱或密码错误"},
        )

    # ⚠️ 账号被封禁 → 拒绝
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "identity.account_suspended", "message": "账号已被停用"},
        )

    return LoginResponse(user=_to_response(user))


# ══════════════════════════════════════════════════════════
# 验证码
# ══════════════════════════════════════════════════════════


@router.post("/verification-code", status_code=status.HTTP_202_ACCEPTED)
async def send_verification_code(
    payload: EmailCodeRequest,
    codes: CodeRepoDep,
) -> dict[str, str]:
    """发送邮箱验证码。

    ⚠️ 无论邮箱是否存在都返回 202 ——
       否则可以用来探测「这个邮箱注册过没有」。
    """
    code = generate_verification_code()
    await codes.store(payload.target, code, payload.purpose)

    # ⚠️ 生产环境这里要真的发信（邮件服务）。
    #    ⚠️ 绝不能把 code 返回给客户端 —— 那是绕过邮箱验证。
    return {"status": "sent"}


@router.post("/verification-code/verify")
async def verify_code(
    payload: VerifyCodeRequest,
    codes: CodeRepoDep,
) -> dict[str, bool]:
    """校验验证码。"""
    ok = await codes.verify_and_consume(payload.target, payload.code, payload.purpose)

    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "identity.invalid_code", "message": "验证码无效或已过期"},
        )

    return {"valid": True}


# ══════════════════════════════════════════════════════════
# 微信
# ══════════════════════════════════════════════════════════


@router.get("/wechat/authorize", response_model=WechatAuthorizeResponse)
async def wechat_authorize() -> WechatAuthorizeResponse:
    """获取微信扫码授权 URL。

    ⚠️ 依赖注入微信配置 —— 生产环境从环境变量读，
       **不能有默认值兜底**（旧实现的教训）。
    """
    provider = _get_wechat_provider()
    state = provider.generate_state()

    return WechatAuthorizeResponse(
        authorize_url=provider.build_authorize_url(state),
        state=state,
    )


@router.post("/wechat/callback", response_model=SignupResponse)
async def wechat_callback(
    payload: WechatCallbackRequest,
    users: UserRepoDep,
) -> SignupResponse:
    """微信回调 —— 扫码授权后被调。

    ⚠️ ⚠️ **CSRF 关键点**：
       state 必须由服务端生成并校验。客户端传什么都不能信。
    """
    provider = _get_wechat_provider()

    try:
        profile = await provider.exchange_code(payload.code, state=payload.state)
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "identity.invalid_credentials", "message": str(error)},
        ) from error

    # 已有这个微信身份 → 直接登录
    existing = await users.get_by_identity(profile.provider, profile.provider_user_id)
    if existing is not None:
        return SignupResponse(status=FlowStatus.COMPLETED.value, user=_to_response(existing))

    # 新用户 —— 走注册流程（微信没邮箱 → 会挂起要求补邮箱）
    result = run_signup("wechat", {"identity": profile.to_identity()})
    _raise_for_status(result.status, result.error)

    if result.user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "identity.failed", "message": "注册未产出用户"},
        )

    await users.save(result.user)
    return SignupResponse(status=result.status.value, user=_to_response(result.user))


def _get_wechat_provider() -> Any:
    """拿微信 Provider —— 从环境变量读配置。

    ⚠️ 没有配置就抛错 —— 绝不静默降级。
    """
    appid = os.environ.get("WECHAT_APPID")
    secret = os.environ.get("WECHAT_SECRET")
    redirect_uri = os.environ.get("WECHAT_REDIRECT_URI")
    state_secret = os.environ.get("IDENTITY_STATE_SECRET")

    missing = [
        name
        for name, value in (
            ("WECHAT_APPID", appid),
            ("WECHAT_SECRET", secret),
            ("WECHAT_REDIRECT_URI", redirect_uri),
            ("IDENTITY_STATE_SECRET", state_secret),
        )
        if not value
    ]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "identity.not_configured",
                "message": f"缺少配置：{', '.join(missing)}",
            },
        )

    return WechatProvider(
        config=WechatConfig(
            appid=appid or "",
            secret=secret or "",
            redirect_uri=redirect_uri or "",
            state_secret=state_secret or "",
        )
    )
