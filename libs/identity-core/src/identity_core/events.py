"""领域事件 —— identity 与下游解耦的关键。

⚠️ 设计意图：**identity 不知道下游有谁**。

   旧系统的做法（反面教材）：
   ```python
   class AccountModel(Base):
       LITELLM_PAY_KEY = ...        # ← 计费密钥塞进身份表
       MASTODON_PASSWORD = ...      # ← 社区密码塞进身份表
   ```
   结果：identity 一改，下游全得跟着改；identity 想复用到别的项目，
   这些字段全得带着走。

   本模块的做法：
   ```python
   @dataclass
   class UserRegistered:
       user_id: UUID
       email: str
       providers: list[str]
   ```
   identity 只发事件；billing / community 各自订阅，自己决定做什么。

   **identity 永远不需要知道 billing 的存在。**
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

__all__ = [
    "IdentityBound",
    "IdentityEvent",
    "UserEmailBound",
    "UserLoggedIn",
    "UserRegistered",
]


@dataclass(frozen=True, slots=True)
class IdentityEvent:
    """领域事件基类。

    ⚠️ 所有事件都必须可序列化（跨进程投递）。
    """

    #: 事件类型 —— 订阅方按它过滤
    event_type: str = "identity.event"

    #: 事件 ID —— 幂等消费用
    event_id: UUID = field(default_factory=uuid4)

    #: 发生时间（UTC）
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    #: 租户 —— 多租户场景下订阅方按它分流
    tenant_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """转成可序列化的字典。"""
        return {
            "event_type": self.event_type,
            "event_id": str(self.event_id),
            "occurred_at": self.occurred_at.isoformat(),
            "tenant_id": self.tenant_id,
            **self.payload(),
        }

    def payload(self) -> dict[str, Any]:
        """子类提供的事件负载。"""
        return {}


@dataclass(frozen=True, slots=True)
class UserRegistered(IdentityEvent):
    """用户注册完成。

    订阅方典型用法：
      · billing  → 建账本账户
      · community → 建社区账号
      · notification → 发欢迎邮件
    """

    event_type: str = "identity.user_registered"

    user_id: UUID | None = None
    email: str | None = None
    phone: str | None = None
    display_name: str | None = None
    providers: tuple[str, ...] = ()

    def payload(self) -> dict[str, Any]:
        """事件负载。"""
        return {
            "user_id": str(self.user_id) if self.user_id else None,
            "email": self.email,
            "phone": self.phone,
            "display_name": self.display_name,
            "providers": list(self.providers),
        }


@dataclass(frozen=True, slots=True)
class UserEmailBound(IdentityEvent):
    """用户绑定了邮箱（并验证通过）。

    订阅方典型用法：
      · notification → 发「邮箱绑定成功」
      · billing       → 允许开启邮件发票
    """

    event_type: str = "identity.user_email_bound"

    user_id: UUID | None = None
    email: str | None = None
    verified: bool = True

    def payload(self) -> dict[str, Any]:
        """事件负载。"""
        return {
            "user_id": str(self.user_id) if self.user_id else None,
            "email": self.email,
            "verified": self.verified,
        }


@dataclass(frozen=True, slots=True)
class UserLoggedIn(IdentityEvent):
    """用户登录成功。

    订阅方典型用法：
      · audit      → 记登录日志
      · notification → 可选：异地登录提醒
    """

    event_type: str = "identity.user_logged_in"

    user_id: UUID | None = None
    provider: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None

    def payload(self) -> dict[str, Any]:
        """事件负载。"""
        return {
            "user_id": str(self.user_id) if self.user_id else None,
            "provider": self.provider,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
        }


@dataclass(frozen=True, slots=True)
class IdentityBound(IdentityEvent):
    """用户绑定了新的第三方身份（如首次微信登录后绑 Google）。

    订阅方典型用法：
      · community → 关联已有社区账号
    """

    event_type: str = "identity.identity_bound"

    user_id: UUID | None = None
    provider: str | None = None
    provider_user_id: str | None = None

    def payload(self) -> dict[str, Any]:
        """事件负载。"""
        return {
            "user_id": str(self.user_id) if self.user_id else None,
            "provider": self.provider,
            "provider_user_id": self.provider_user_id,
        }
