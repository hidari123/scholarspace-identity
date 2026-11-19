"""内存存储实现 —— 用于开发与测试。

⚠️ 刻意实现成**线程安全**（用 Lock）——
   测试里多个 async 任务并发跑时，不加锁会有偶发失败。

生产环境用 PostgreSQL 实现（见 README），接口完全一致。
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from uuid import UUID

from identity_core.entities import Credential, CredentialType, Identity, ProviderType, User

__all__ = [
    "InMemoryCredentialRepository",
    "InMemoryUserRepository",
    "InMemoryVerificationCodeRepository",
]


@dataclass
class _VerificationEntry:
    """一条验证码记录。"""

    code: str
    expires_at: datetime


class InMemoryUserRepository:
    """内存用户表。"""

    def __init__(self) -> None:
        """初始化。"""
        self._users: dict[UUID, User] = {}
        self._lock = asyncio.Lock()

    async def get(self, user_id: UUID) -> User | None:
        """按 ID 查用户。"""
        async with self._lock:
            return self._users.get(user_id)

    async def get_by_email(self, email: str) -> User | None:
        """按邮箱查用户。

        ⚠️ 邮箱要先小写归一 —— 与领域层 EmailAddress 规则一致，
           否则 `A@B.com` 和 `a@b.com` 会是两个用户。
        """
        normalized = email.strip().lower()
        async with self._lock:
            for user in self._users.values():
                if user.email is not None and user.email.value == normalized:
                    return user
        return None

    async def get_by_identity(
        self,
        provider: ProviderType,
        provider_user_id: str,
    ) -> User | None:
        """按第三方身份查用户。"""
        async with self._lock:
            for user in self._users.values():
                if user.find_identity(provider, provider_user_id) is not None:
                    return user
        return None

    async def save(self, user: User) -> User:
        """保存用户。"""
        async with self._lock:
            self._users[user.user_id] = user
            return user

    async def exists_by_email(self, email: str) -> bool:
        """邮箱是否已被占用。"""
        return await self.get_by_email(email) is not None

    async def count(self) -> int:
        """用户总数。"""
        async with self._lock:
            return len(self._users)


class InMemoryCredentialRepository:
    """内存凭证表。"""

    def __init__(self) -> None:
        """初始化。"""
        self._credentials: list[Credential] = []
        self._lock = asyncio.Lock()

    async def get_by_user_and_type(
        self,
        user_id: UUID,
        credential_type: CredentialType,
    ) -> Credential | None:
        """按用户 + 类型查凭证。"""
        async with self._lock:
            for credential in self._credentials:
                if credential.user_id == user_id and credential.credential_type == credential_type:
                    return credential
        return None

    async def get_oauth_credential(
        self,
        user_id: UUID,
        provider: ProviderType,
    ) -> Credential | None:
        """按用户 + 第三方平台查 OAuth 凭证。

        ⚠️ OAuth 凭证的 tokens 里存着 provider 标识，
           所以要比对 tokens["provider"]。
        """
        async with self._lock:
            for credential in self._credentials:
                if (
                    credential.user_id == user_id
                    and credential.credential_type == CredentialType.OAUTH_TOKEN
                    and credential.tokens.get("provider") == provider.value
                ):
                    return credential
        return None

    async def save(self, credential: Credential) -> Credential:
        """保存凭证（同类型同用户的覆盖旧的）。"""
        async with self._lock:
            for index, existing in enumerate(self._credentials):
                if (
                    existing.user_id == credential.user_id
                    and existing.credential_type == credential.credential_type
                    and existing.tokens.get("provider") == credential.tokens.get("provider")
                ):
                    self._credentials[index] = credential
                    return credential

            self._credentials.append(credential)
            return credential

    async def delete(self, user_id: UUID, credential_type: CredentialType) -> None:
        """删除凭证。"""
        async with self._lock:
            self._credentials = [
                credential
                for credential in self._credentials
                if not (
                    credential.user_id == user_id and credential.credential_type == credential_type
                )
            ]


class InMemoryVerificationCodeRepository:
    """内存验证码表。"""

    def __init__(self) -> None:
        """初始化。"""
        self._codes: dict[tuple[str, str], _VerificationEntry] = {}
        self._lock = asyncio.Lock()

    async def store(
        self,
        target: str,
        code: str,
        purpose: str,
        ttl_seconds: int = 300,
    ) -> None:
        """存验证码。

        ⚠️ key 含 purpose —— 「注册用码」和「改密码用码」互不干扰。
        """
        expires_at = datetime.now(UTC) + timedelta(seconds=ttl_seconds)
        async with self._lock:
            self._codes[(target, purpose)] = _VerificationEntry(code=code, expires_at=expires_at)

    async def verify_and_consume(self, target: str, code: str, purpose: str) -> bool:
        """校验并消费验证码。

        ⚠️ **一次性** —— 校验通过后立即删除，
           同一个码不能被重复使用。
        """
        key = (target, purpose)
        async with self._lock:
            entry = self._codes.get(key)
            if entry is None:
                return False

            # 过期就清掉
            if datetime.now(UTC) > entry.expires_at:
                del self._codes[key]
                return False

            if entry.code != code:
                return False

            # ✅ 消费掉 —— 一次性
            del self._codes[key]
            return True

    async def invalidate(self, target: str, purpose: str) -> None:
        """作废某用途下的所有验证码。"""
        async with self._lock:
            self._codes.pop((target, purpose), None)


@dataclass
class InMemoryRepositories:
    """三个仓储的容器 —— 方便整体注入。"""

    users: InMemoryUserRepository = field(default_factory=InMemoryUserRepository)
    credentials: InMemoryCredentialRepository = field(default_factory=InMemoryCredentialRepository)
    verification_codes: InMemoryVerificationCodeRepository = field(
        default_factory=InMemoryVerificationCodeRepository
    )


def build_identity(user: User, provider: ProviderType, provider_user_id: str) -> Identity:
    """给用户造一个身份（测试辅助）。"""
    return Identity(
        provider=provider,
        provider_user_id=provider_user_id,
        user_id=user.user_id,
    )
