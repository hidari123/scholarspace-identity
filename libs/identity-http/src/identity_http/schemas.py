"""HTTP 请求/响应模型。

⚠️ 用 Pydantic v2 —— 校验在入口做，领域层拿到的数据已经干净。

⚠️ 错误响应遵循主仓的契约（contracts/openapi/common.yaml）：
    {
      "data": {...},
      "meta": {...},
      "error": {"code": "...", "message": "...", "details": {...}}
    }
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

__all__ = [
    "EmailCodeRequest",
    "ErrorDetail",
    "ErrorResponse",
    "LoginRequest",
    "LoginResponse",
    "Meta",
    "SignupRequest",
    "SignupResponse",
    "UserResponse",
    "VerifyCodeRequest",
    "WechatAuthorizeResponse",
    "WechatCallbackRequest",
]


class Meta(BaseModel):
    """响应元信息。"""

    model_config = ConfigDict(extra="forbid")

    request_id: str | None = None


class ErrorDetail(BaseModel):
    """错误详情。"""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(description="错误码，如 identity.email_taken")
    message: str = Field(description="可读的错误说明")
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """错误响应体。"""

    model_config = ConfigDict(extra="forbid")

    error: ErrorDetail
    meta: Meta = Field(default_factory=Meta)


class UserResponse(BaseModel):
    """用户信息。

    ⚠️ **绝不含密码哈希、第三方 token** —— 这些是内部字段。
    """

    model_config = ConfigDict(extra="forbid")

    user_id: UUID
    email: str | None = None
    email_verified: bool = False
    phone: str | None = None
    phone_verified: bool = False
    display_name: str | None = None
    avatar_url: str | None = None
    providers: list[str] = Field(default_factory=list)
    created_at: str


class SignupRequest(BaseModel):
    """注册请求。

    ⚠️ 邮箱注册与第三方注册用**不同**的请求体 ——
       第三方注册不带密码（密码由 provider 侧管理）。
    """

    model_config = ConfigDict(extra="forbid")

    method: str = Field(description="注册方式：email / wechat / google / github / sms")
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=10, max_length=128)
    phone: str | None = None
    display_name: str | None = Field(default=None, max_length=64)


class SignupResponse(BaseModel):
    """注册响应。"""

    model_config = ConfigDict(extra="forbid")

    status: str = Field(description="completed / pending / failed")
    user: UserResponse | None = None
    #: pending 时告诉前端下一步做什么（如绑定邮箱）
    next_step: str | None = None
    #: pending 时给前端的提示（i18n key）
    reason: str | None = None


class LoginRequest(BaseModel):
    """登录请求。"""

    model_config = ConfigDict(extra="forbid")

    method: str = Field(description="登录方式")
    email: EmailStr | None = None
    password: str | None = Field(default=None, max_length=128)
    phone: str | None = None
    code: str | None = Field(default=None, max_length=8)


class LoginResponse(BaseModel):
    """登录响应。"""

    model_config = ConfigDict(extra="forbid")

    user: UserResponse
    #: 内部 token —— 由 auth 服务签发，identity 只透传
    access_token: str | None = None
    token_type: str = "Bearer"  # noqa: S105
    expires_in: int | None = None


class EmailCodeRequest(BaseModel):
    """发送验证码请求。"""

    model_config = ConfigDict(extra="forbid")

    target: EmailStr = Field(description="收信邮箱")
    purpose: str = Field(
        default="register",
        description="用途：register / reset_password / bind_email",
    )


class VerifyCodeRequest(BaseModel):
    """校验验证码请求。"""

    model_config = ConfigDict(extra="forbid")

    target: EmailStr
    code: str = Field(min_length=4, max_length=8)
    purpose: str = "register"


class WechatAuthorizeResponse(BaseModel):
    """微信授权 URL 响应。"""

    model_config = ConfigDict(extra="forbid")

    authorize_url: str
    state: str = Field(description="防 CSRF 的 state —— 前端需原样带回")


class WechatCallbackRequest(BaseModel):
    """微信回调参数。"""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1)
    state: str = Field(min_length=1)
