"""存储端口 —— 领域层与应用层之间的契约。

⚠️ 端口定义在**应用层**（application），实现放在**基础设施层**（infrastructure）。

这样做的目的：
  · 领域/应用层不依赖 SQLAlchemy —— 换数据库不用改业务逻辑
  · 测试可以塞内存实现，不用起数据库
  · 符合 ADR 的四层架构（domain → application → infrastructure → interfaces）
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable
from uuid import UUID

from identity_core.entities import Credential, CredentialType, ProviderType, User

__all__ = ["CredentialRepository", "UserRepository", "VerificationCodeRepository"]


@runtime_checkable
class UserRepository(Protocol):
    """用户表存储端口。"""

    async def get(self, user_id: UUID) -> User | None:
        """按 ID 查用户。

        Args:
            user_id: 用户 ID

        Returns:
            用户，不存在返回 None
        """
        ...

    async def get_by_email(self, email: str) -> User | None:
        """按邮箱查用户。

        ⚠️ 邮箱要先小写归一 —— 与领域层的 EmailAddress 规则一致。
        """
        ...

    async def get_by_identity(
        self,
        provider: ProviderType,
        provider_user_id: str,
    ) -> User | None:
        """按第三方身份查用户。

        ⚠️ 这是「用微信登录」的关键查询 ——
           用 provider_user_id（openid），不是昵称。
        """
        ...

    async def save(self, user: User) -> User:
        """保存用户（新增或更新）。"""
        ...

    async def exists_by_email(self, email: str) -> bool:
        """邮箱是否已被占用。"""
        ...

    async def count(self) -> int:
        """用户总数 —— 管理后台用。"""
        ...


@runtime_checkable
class CredentialRepository(Protocol):
    """凭证表存储端口。"""

    async def get_by_user_and_type(
        self,
        user_id: UUID,
        credential_type: CredentialType,
    ) -> Credential | None:
        """按用户 + 类型查凭证。

        ⚠️ 一个用户可以有多条 OAuth 凭证（微信 + Google），
           所以还要能按 provider 细分 —— 见 get_oauth_credential。
        """
        ...

    async def get_oauth_credential(
        self,
        user_id: UUID,
        provider: ProviderType,
    ) -> Credential | None:
        """按用户 + 第三方平台查 OAuth 凭证。"""
        ...

    async def save(self, credential: Credential) -> Credential:
        """保存凭证。"""
        ...

    async def delete(self, user_id: UUID, credential_type: CredentialType) -> None:
        """删除凭证。"""
        ...


@runtime_checkable
class VerificationCodeRepository(Protocol):
    """验证码存储端口（邮箱/短信验证码）。

    ⚠️ 需要支持「按用途查询」——
       「注册用验证码」和「改密码用验证码」即使码相同也不能混用。
    """

    async def store(
        self,
        target: str,
        code: str,
        purpose: str,
        ttl_seconds: int = 300,
    ) -> None:
        """存验证码。

        Args:
            target: 邮箱或手机号
            code: 验证码
            purpose: 用途（register / reset_password / bind_email）
            ttl_seconds: 有效期
        """
        ...

    async def verify_and_consume(self, target: str, code: str, purpose: str) -> bool:
        """校验并消费验证码。

        ⚠️ **一次性** —— 校验通过后立即作废，
           否则同一个码能被反复使用。
        """
        ...

    async def invalidate(self, target: str, purpose: str) -> None:
        """作废某用途下的所有验证码。"""
        ...
