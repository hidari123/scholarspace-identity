"""身份领域模型 —— 纯领域，零外部依赖。

⚠️ 本模块**不知道**任何下游的存在（billing / community / paper…）。
   它只发领域事件，由订阅方决定要做什么。

   这正是旧系统 `ACCOUNT` 表的教训 —— 那里把 LITELLM_PAY_KEY、
   MASTODON_PASSWORD 等业务字段全塞进了身份表。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

__all__ = [
    "Credential",
    "CredentialType",
    "EmailAddress",
    "Identity",
    "InvalidEmailError",
    "InvalidPhoneError",
    "PhoneNumber",
    "ProviderType",
    "User",
]


class InvalidEmailError(ValueError):
    """邮箱格式非法。"""


class InvalidPhoneError(ValueError):
    """手机号格式非法。"""


#: 邮箱正则 —— 刻意宽松。真正的验证靠「发验证码」，不靠正则。
#: 过严的正则会误杀合法邮箱（+标签、国际化域名、新域名后缀）。
_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

#: 手机号 —— 中国大陆 11 位（1 开头）。
_PHONE_PATTERN = re.compile(r"^1[3-9]\d{9}$")


@dataclass(frozen=True, slots=True)
class EmailAddress:
    """邮箱地址。

    ⚠️ `verified` 是**领域状态**，不是存储细节 ——
       「邮箱必绑」Policy 依赖它。
    """

    value: str
    verified: bool = False

    def __post_init__(self) -> None:
        """校验格式。"""
        normalized = self.value.strip().lower()
        if not _EMAIL_PATTERN.match(normalized):
            raise InvalidEmailError(f"邮箱格式非法：{self.value}")

        object.__setattr__(self, "value", normalized)

    def mark_verified(self) -> EmailAddress:
        """标记为已验证。"""
        return EmailAddress(value=self.value, verified=True)

    def __str__(self) -> str:
        """字符串表示。"""
        return self.value


@dataclass(frozen=True, slots=True)
class PhoneNumber:
    """手机号（中国大陆）。"""

    value: str
    verified: bool = False

    def __post_init__(self) -> None:
        """校验格式。"""
        normalized = self.value.strip().replace(" ", "").replace("-", "")
        if not _PHONE_PATTERN.match(normalized):
            raise InvalidPhoneError(f"手机号格式非法：{self.value}")

        object.__setattr__(self, "value", normalized)

    def mark_verified(self) -> PhoneNumber:
        """标记为已验证。"""
        return PhoneNumber(value=self.value, verified=True)

    def __str__(self) -> str:
        """字符串表示。"""
        return self.value


class ProviderType(StrEnum):
    """登录方式。"""

    EMAIL_PASSWORD = "email_password"  # noqa: S105
    WECHAT = "wechat"
    GOOGLE = "google"
    GITHUB = "github"
    SMS = "sms"


class CredentialType(StrEnum):
    """凭证类型。"""

    PASSWORD = "password"  # noqa: S105
    OAUTH_TOKEN = "oauth_token"  # noqa: S105
    SMS_CODE = "sms_code"


@dataclass(frozen=True, slots=True)
class Identity:
    """身份 —— 一个用户在某个第三方平台的账号。

    ⚠️ User 与 Identity 是 1:N。
       一个人可以同时用「微信 + Google + 邮箱」登录，User 是同一个。

    关键字段是 `provider_user_id`（如微信 openid），**不是昵称** ——
    昵称会变，openid 不会。
    """

    provider: ProviderType
    provider_user_id: str
    user_id: UUID | None = None
    display_name: str | None = None
    avatar_url: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """校验 provider_user_id 非空。"""
        if not self.provider_user_id.strip():
            raise ValueError("provider_user_id 不能为空")

    def bind_to(self, user_id: UUID) -> Identity:
        """绑定到某个用户。"""
        return Identity(
            provider=self.provider,
            provider_user_id=self.provider_user_id,
            user_id=user_id,
            display_name=self.display_name,
            avatar_url=self.avatar_url,
            raw=self.raw,
        )


@dataclass(frozen=True, slots=True)
class Credential:
    """凭证 —— 用户的登录凭据。"""

    user_id: UUID
    credential_type: CredentialType
    #: 密码哈希（argon2/bcrypt）—— **绝不存明文**
    secret_hash: str | None = None
    #: 第三方 access/refresh token
    tokens: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_used_at: datetime | None = None

    def touch(self) -> Credential:
        """更新最后使用时间。"""
        return Credential(
            user_id=self.user_id,
            credential_type=self.credential_type,
            secret_hash=self.secret_hash,
            tokens=self.tokens,
            created_at=self.created_at,
            last_used_at=datetime.now(UTC),
        )


@dataclass(frozen=True, slots=True)
class User:
    """用户。

    ⚠️ 只包含**身份**信息。业务数据（额度、论文、社区账号）在别的包。
    """

    user_id: UUID
    email: EmailAddress | None = None
    phone: PhoneNumber | None = None
    display_name: str | None = None
    avatar_url: str | None = None
    identities: tuple[Identity, ...] = ()
    tenant_id: str | None = None
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def create(
        cls,
        *,
        email: EmailAddress | None = None,
        phone: PhoneNumber | None = None,
        display_name: str | None = None,
        avatar_url: str | None = None,
        tenant_id: str | None = None,
    ) -> User:
        """创建用户。"""
        return cls(
            user_id=uuid4(),
            email=email,
            phone=phone,
            display_name=display_name,
            avatar_url=avatar_url,
            tenant_id=tenant_id,
        )

    @property
    def has_verified_email(self) -> bool:
        """是否已验证邮箱。"""
        return self.email is not None and self.email.verified

    @property
    def providers(self) -> tuple[ProviderType, ...]:
        """已绑定的登录方式。"""
        return tuple(identity.provider for identity in self.identities)

    def with_identity(self, identity: Identity) -> User:
        """绑定一个身份。"""
        return User(
            user_id=self.user_id,
            email=self.email,
            phone=self.phone,
            display_name=self.display_name,
            avatar_url=self.avatar_url,
            identities=(*self.identities, identity.bind_to(self.user_id)),
            tenant_id=self.tenant_id,
            is_active=self.is_active,
            created_at=self.created_at,
            updated_at=datetime.now(UTC),
        )

    def with_email(self, email: EmailAddress) -> User:
        """设置邮箱。"""
        return User(
            user_id=self.user_id,
            email=email,
            phone=self.phone,
            display_name=self.display_name,
            avatar_url=self.avatar_url,
            identities=self.identities,
            tenant_id=self.tenant_id,
            is_active=self.is_active,
            created_at=self.created_at,
            updated_at=datetime.now(UTC),
        )

    def with_phone(self, phone: PhoneNumber) -> User:
        """设置手机号。"""
        return User(
            user_id=self.user_id,
            email=self.email,
            phone=phone,
            display_name=self.display_name,
            avatar_url=self.avatar_url,
            identities=self.identities,
            tenant_id=self.tenant_id,
            is_active=self.is_active,
            created_at=self.created_at,
            updated_at=datetime.now(UTC),
        )

    def find_identity(
        self,
        provider: ProviderType,
        provider_user_id: str,
    ) -> Identity | None:
        """按 provider + provider_user_id 查找身份。

        ⚠️ 微信必须用 `provider_user_id`（openid）而不是昵称 ——
           昵称会变，openid 不会。
        """
        for identity in self.identities:
            if identity.provider == provider and identity.provider_user_id == provider_user_id:
                return identity
        return None
