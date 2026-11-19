"""Provider 协议 —— 各登录方式的统一抽象。

⚠️ Provider 分两类：

    OAuth 类（微信 / Google / GitHub）
      → 第三方授权 → 拿 provider_user_id（openid / sub）
      → 用户可能**没有邮箱**（微信）或**有邮箱**（Google/GitHub）

    凭证类（邮箱密码 / 短信）
      → 直接验证用户输入
      → 邮箱必须验证（验证码）

统一抽象让上层（流程引擎）不需要知道具体是哪种。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from identity_core.entities import Identity, ProviderType

__all__ = [
    "CredentialProvider",
    "EmailUnavailableError",
    "InvalidCredentialError",
    "OAuthProfile",
    "OAuthProvider",
    "ProviderError",
    "ProviderProfile",
]


class ProviderError(Exception):
    """Provider 调用失败。"""


class InvalidCredentialError(ProviderError):
    """凭证无效（密码错、验证码错、state 不匹配）。"""


class EmailUnavailableError(ProviderError):
    """该 Provider 拿不到邮箱（如微信）。"""


@dataclass(frozen=True, slots=True)
class ProviderProfile:
    """Provider 返回的用户档案。"""

    #: Provider 类型
    provider: ProviderType

    #: ⭐ 第三方唯一标识（微信 openid / Google sub / GitHub id）
    #: ⚠️ 绝不能用昵称或邮箱代替 —— 昵称会变
    provider_user_id: str

    #: 昵称 / 显示名
    display_name: str | None = None

    #: 头像 URL
    avatar_url: str | None = None

    #: 邮箱（可能为 None）
    email: str | None = None

    #: 邮箱是否已由 Provider 验证过
    email_verified: bool = False

    #: 第三方原始数据（保留以便排查）
    raw: dict[str, Any] = field(default_factory=dict)

    def to_identity(self) -> Identity:
        """转成领域身份对象。"""
        return Identity(
            provider=self.provider,
            provider_user_id=self.provider_user_id,
            display_name=self.display_name,
            avatar_url=self.avatar_url,
            raw=self.raw,
        )


@dataclass(frozen=True, slots=True)
class OAuthProfile(ProviderProfile):
    """OAuth 类 Provider 的档案。"""

    #: 第三方 access token（后续 API 调用用）
    access_token: str | None = None

    #: 第三方 refresh token
    refresh_token: str | None = None

    #: token 过期时间（unix 秒）
    expires_at: int | None = None


@runtime_checkable
class OAuthProvider(Protocol):
    """OAuth 类 Provider 协议。"""

    #: Provider 类型
    provider_type: ProviderType

    #: 授权端点
    authorize_url: str

    #: 回调地址
    redirect_uri: str

    def build_authorize_url(self, state: str) -> str:
        """构造授权跳转 URL。

        Args:
            state: 防 CSRF 的随机串（**必须**由服务端生成并签名）
        """
        ...

    async def exchange_code(self, code: str, state: str | None = None) -> OAuthProfile:
        """用 code 换取用户档案。

        Args:
            code: 第三方回调带来的授权码
            state: 回传的 state —— 用于校验防 CSRF

        Raises:
            InvalidCredentialError: state 不匹配或 code 无效
            ProviderError: 第三方调用失败
        """
        ...


@runtime_checkable
class CredentialProvider(Protocol):
    """凭证类 Provider 协议（邮箱密码 / 短信）。"""

    #: Provider 类型
    provider_type: ProviderType

    async def verify(self, credential: str, **kwargs: Any) -> ProviderProfile:
        """验证凭证。

        Args:
            credential: 用户输入（密码 / 验证码）
            kwargs: 额外参数（如 password_hash / email）

        Raises:
            InvalidCredentialError: 凭证错误
        """
        ...
