"""Policy 机制测试。"""

from __future__ import annotations

from identity_core.entities import EmailAddress, PhoneNumber, User
from identity_core.policy import (
    EmailRequiredPolicy,
    PhoneRequiredPolicy,
    PolicyAction,
    evaluate_policies,
)


class TestEmailRequiredPolicy:
    """邮箱必绑策略。"""

    def test_requires_email_when_user_missing(self) -> None:
        """还没有用户 → 要求邮箱。"""
        decision = EmailRequiredPolicy().evaluate(None)

        assert decision.action is PolicyAction.REQUIRE_STAGE
        assert decision.stage == "email_verification"
        assert decision.reason is not None

    def test_requires_email_when_unverified(self) -> None:
        """有邮箱但没验证 → 要求验证。"""
        user = User.create(email=EmailAddress("a@b.com"))

        decision = EmailRequiredPolicy().evaluate(user)

        assert decision.action is PolicyAction.REQUIRE_STAGE
        assert decision.stage == "email_verification"

    def test_passes_when_verified(self) -> None:
        """邮箱已验证 → 通过。"""
        user = User.create(email=EmailAddress("a@b.com").mark_verified())

        decision = EmailRequiredPolicy().evaluate(user)

        assert decision.action is PolicyAction.CONTINUE

    def test_requires_when_no_email_at_all(self) -> None:
        """微信注册（无邮箱）→ 要求补邮箱。"""
        user = User.create()

        decision = EmailRequiredPolicy().evaluate(user)

        assert decision.action is PolicyAction.REQUIRE_STAGE


class TestPhoneRequiredPolicy:
    """手机号必绑策略。"""

    def test_requires_when_missing(self) -> None:
        """没手机号 → 要求。"""
        decision = PhoneRequiredPolicy().evaluate(User.create())

        assert decision.action is PolicyAction.REQUIRE_STAGE
        assert decision.stage == "sms_verification"

    def test_passes_when_verified(self) -> None:
        """手机号已验证 → 通过。"""
        user = User.create(phone=PhoneNumber("13800138000").mark_verified())

        assert PhoneRequiredPolicy().evaluate(user).action is PolicyAction.CONTINUE


class TestEvaluatePolicies:
    """策略组合。"""

    def test_empty_policies_passes(self) -> None:
        """没有策略 → 通过。"""
        assert evaluate_policies([], None).action is PolicyAction.CONTINUE

    def test_first_non_continue_wins(self) -> None:
        """短路：任一策略要求 stage 就停。"""
        policies = [
            EmailRequiredPolicy(),
            PhoneRequiredPolicy(),
        ]

        decision = evaluate_policies(policies, User.create())

        assert decision.action is PolicyAction.REQUIRE_STAGE
        assert decision.stage == "email_verification"

    def test_all_pass_continues(self) -> None:
        """全部通过 → continue。"""
        user = User.create(
            email=EmailAddress("a@b.com").mark_verified(),
            phone=PhoneNumber("13800138000").mark_verified(),
        )
        policies = [EmailRequiredPolicy(), PhoneRequiredPolicy()]

        assert evaluate_policies(policies, user).action is PolicyAction.CONTINUE

    def test_policy_order_is_priority(self) -> None:
        """策略顺序即优先级。"""
        policies = [PhoneRequiredPolicy(), EmailRequiredPolicy()]
        user = User.create(email=EmailAddress("a@b.com").mark_verified())

        decision = evaluate_policies(policies, user)

        # phone 先跑 → phone 没满足 → 要求 phone
        assert decision.stage == "sms_verification"
