"""Policy 机制 —— 借鉴 authentik 的架构思想。

⚠️ 为什么要 Policy 而不是把规则写死在流程里：

   「邮箱必绑」是一条**业务策略**，不同租户可能要求不同
   （个人站强制邮箱，企业 SSO 站可能允许只绑手机号）。

   写成 Policy 后：
   · 规则集中可测
   · 换租户只要换 Policy 组合，不改流程代码
   · 策略可组合、可优先级排序

设计源自 authentik 的 policy 机制，**实现完全自研**。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, ClassVar, Protocol, runtime_checkable

if TYPE_CHECKING:
    from identity_core.entities import User

__all__ = [
    "EmailRequiredPolicy",
    "PhoneRequiredPolicy",
    "Policy",
    "PolicyAction",
    "PolicyDecision",
    "evaluate_policies",
]


class PolicyAction(StrEnum):
    """策略动作。"""

    #: 继续下一个 stage
    CONTINUE = "continue"
    #: 要求执行某个 stage
    REQUIRE_STAGE = "require_stage"
    #: 拒绝
    DENY = "deny"


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    """策略决策。"""

    action: PolicyAction
    #: action=REQUIRE_STAGE 时，要执行的 stage 类型标识
    stage: str | None = None
    #: 拒绝原因（i18n key）
    reason: str | None = None

    @classmethod
    def ok(cls) -> PolicyDecision:
        """继续。"""
        return cls(action=PolicyAction.CONTINUE)

    @classmethod
    def require(cls, stage: str, reason: str | None = None) -> PolicyDecision:
        """要求执行某个 stage。"""
        return cls(action=PolicyAction.REQUIRE_STAGE, stage=stage, reason=reason)

    @classmethod
    def deny(cls, reason: str) -> PolicyDecision:
        """拒绝。"""
        return cls(action=PolicyAction.DENY, reason=reason)


@runtime_checkable
class Policy(Protocol):
    """策略协议。

    实现类只需提供 `evaluate`。
    """

    #: 策略 ID —— 用于排序与调试
    #:
    #: ⚠️ 用 ClassVar —— 实现类是 dataclass，这是类级常量不是实例状态。
    policy_id: ClassVar[str]

    def evaluate(self, user: User | None) -> PolicyDecision:
        """评估策略。

        Args:
            user: 当前用户（注册流程中可能为 None）

        Returns:
            决策
        """
        ...


@dataclass(frozen=True, slots=True)
class EmailRequiredPolicy:
    """邮箱必绑。

    ⚠️ 微信注册的用户没有邮箱 —— 这条策略会强制他们补邮箱并验证。
    """

    policy_id: ClassVar[str] = "email_required"

    def evaluate(self, user: User | None) -> PolicyDecision:
        """评估。"""
        if user is None:
            return PolicyDecision.require(
                stage="email_verification",
                reason="common.identity.error.email_required",
            )

        if user.has_verified_email:
            return PolicyDecision.ok()

        return PolicyDecision.require(
            stage="email_verification",
            reason="common.identity.error.email_required",
        )


@dataclass(frozen=True, slots=True)
class PhoneRequiredPolicy:
    """手机号必绑（可选策略，按租户要求开启）。"""

    policy_id: ClassVar[str] = "phone_required"

    def evaluate(self, user: User | None) -> PolicyDecision:
        """评估。"""
        if user is not None and user.phone is not None and user.phone.verified:
            return PolicyDecision.ok()

        return PolicyDecision.require(
            stage="sms_verification",
            reason="common.identity.error.phone_required",
        )


def evaluate_policies(
    policies: list[Policy],
    user: User | None,
) -> PolicyDecision:
    """依次评估所有策略。

    ⚠️ 短路语义：任一策略要求 stage 或拒绝，就不再评估后面的。
       策略顺序即优先级。
    """
    for policy in policies:
        decision = policy.evaluate(user)
        if decision.action is not PolicyAction.CONTINUE:
            return decision

    return PolicyDecision.ok()
