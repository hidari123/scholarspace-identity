"""scholarspace-identity-http —— HTTP 接口层。

⚠️ 公开 API 只从这里导出。
"""

from identity_http.app import create_app
from identity_http.ports import (
    CredentialRepository,
    UserRepository,
    VerificationCodeRepository,
)
from identity_http.schemas import (
    EmailCodeRequest,
    ErrorDetail,
    ErrorResponse,
    LoginRequest,
    LoginResponse,
    Meta,
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

__version__ = "0.1.0"

__all__ = [
    # 端口
    "CredentialRepository",
    # 模型
    "EmailCodeRequest",
    "ErrorDetail",
    "ErrorResponse",
    # 内存实现
    "InMemoryCredentialRepository",
    "InMemoryUserRepository",
    "InMemoryVerificationCodeRepository",
    "LoginRequest",
    "LoginResponse",
    "Meta",
    "SignupRequest",
    "SignupResponse",
    "UserRepository",
    "UserResponse",
    "VerificationCodeRepository",
    "VerifyCodeRequest",
    "WechatAuthorizeResponse",
    "WechatCallbackRequest",
    "__version__",
    # 应用
    "create_app",
]
