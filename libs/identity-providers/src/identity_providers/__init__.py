"""scholarspace-identity-providers —— 各登录方式的适配。

⚠️ 公开 API 只从这里导出。
"""

from identity_providers.base import (
    CredentialProvider,
    EmailUnavailableError,
    InvalidCredentialError,
    OAuthProfile,
    OAuthProvider,
    ProviderError,
    ProviderProfile,
)
from identity_providers.oauth2.standard import (
    GitHubProvider,
    GoogleProvider,
    OAuth2Config,
)
from identity_providers.oauth2.state import OAuth2StateCodec
from identity_providers.oauth2.wechat import WechatConfig, WechatOAuthError, WechatProvider
from identity_providers.password.email_password import (
    Argon2Hasher,
    BcryptHasher,
    EmailPasswordProvider,
    PasswordHasher,
    generate_verification_code,
)

__version__ = "0.1.0"

__all__ = [
    # 密码
    "Argon2Hasher",
    "BcryptHasher",
    # 基础
    "CredentialProvider",
    "EmailPasswordProvider",
    "EmailUnavailableError",
    # 标准 OAuth2
    "GitHubProvider",
    "GoogleProvider",
    "InvalidCredentialError",
    "OAuth2Config",
    "OAuth2StateCodec",
    "OAuthProfile",
    "OAuthProvider",
    "PasswordHasher",
    "ProviderError",
    "ProviderProfile",
    # 微信
    "WechatConfig",
    "WechatOAuthError",
    "WechatProvider",
    "__version__",
    "generate_verification_code",
]
