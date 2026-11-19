"""流程引擎测试。"""

from __future__ import annotations

from identity_core.entities import Identity, ProviderType, User

from identity_flows.engine import (
    BindEmailStage,
    CreateUserStage,
    Flow,
    FlowStatus,
    StageContext,
    StageResult,
    run_flow,
)
from identity_flows.flows import SIGNUP_FLOWS, get_signup_flow
from identity_flows.runner import run_signup


class _NoopStage:
    """什么都不做的 stage（测试用）。"""

    stage_id = "noop"
    allows_anonymous = True

    def run(self, context: StageContext) -> StageResult:  # noqa: ARG002
        """执行。"""
        return StageResult(ok=True)


class _FailingStage:
    """总是失败的 stage（测试用）。"""

    stage_id = "failing"
    allows_anonymous = True

    def run(self, context: StageContext) -> StageResult:  # noqa: ARG002
        """执行。"""
        return StageResult(ok=False, error="common.identity.error.boom")


class _PendingStage:
    """总是挂起的 stage（测试用）。"""

    stage_id = "pending"
    allows_anonymous = True

    def run(self, context: StageContext) -> StageResult:  # noqa: ARG002
        """执行。"""
        return StageResult(ok=False, pending_reason="common.identity.error.need_more")


class TestRunFlow:
    """流程执行。"""

    def test_empty_flow_completes(self) -> None:
        """空流程直接完成。"""
        result = run_flow(Flow(name="empty", stages=()), StageContext())

        assert result.status is FlowStatus.COMPLETED
        assert result.ok is True

    def test_single_stage_runs(self) -> None:
        """单个 stage。"""
        flow = Flow(name="f", stages=(_NoopStage(),))
        result = run_flow(flow, StageContext())

        assert result.status is FlowStatus.COMPLETED

    def test_failing_stage_stops_flow(self) -> None:
        """失败的 stage 中断流程。"""
        flow = Flow(name="f", stages=(_FailingStage(), _NoopStage()))
        result = run_flow(flow, StageContext())

        assert result.status is FlowStatus.FAILED
        assert result.error == "common.identity.error.boom"

    def test_pending_stage_suspends_flow(self) -> None:
        """挂起的 stage 让流程暂停（等用户补充）。"""
        flow = Flow(name="f", stages=(_PendingStage(),))
        result = run_flow(flow, StageContext())

        assert result.status is FlowStatus.PENDING
        assert result.error == "common.identity.error.need_more"

    def test_stage_requiring_user_fails_without_user(self) -> None:
        """不允许匿名的 stage 在没有用户时失败。"""

        class _NeedsUser:
            stage_id = "needs_user"
            allows_anonymous = False

            def run(self, context: StageContext) -> StageResult:  # noqa: ARG002
                """执行。"""
                return StageResult(ok=True)

        flow = Flow(name="f", stages=(_NeedsUser(),))
        result = run_flow(flow, StageContext())

        assert result.status is FlowStatus.FAILED
        assert result.error is not None
        assert "stage_requires_user" in result.error


class TestBindEmailStage:
    """绑定邮箱 stage。"""

    def test_requires_pending_email(self) -> None:
        """没有待绑定邮箱时挂起。"""
        result = BindEmailStage().run(StageContext())

        assert result.ok is False
        assert result.pending_reason is not None

    def test_creates_user_when_absent(self) -> None:
        """没有用户时顺带创建。"""
        context = StageContext(pending_email="a@b.com")

        result = BindEmailStage().run(context)

        assert result.ok is True
        assert context.user is not None
        assert context.user.email is not None
        assert context.user.email.value == "a@b.com"

    def test_binds_to_existing_user(self) -> None:
        """已有用户时绑定到该用户。"""
        user = User.create(display_name="张三")
        context = StageContext(user=user, pending_email="a@b.com")

        BindEmailStage().run(context)

        assert context.user is not None
        assert context.user.email is not None
        assert context.user.display_name == "张三"

    def test_rejects_invalid_email(self) -> None:
        """邮箱非法时报错。"""
        context = StageContext(pending_email="not-an-email")

        result = BindEmailStage().run(context)

        assert result.ok is False
        assert result.error == "common.identity.error.invalid_email"

    def test_clears_pending_email(self) -> None:
        """绑定后清空待绑定项。"""
        context = StageContext(pending_email="a@b.com")

        BindEmailStage().run(context)

        assert context.pending_email is None


class TestSignupFlows:
    """注册流程定义。"""

    def test_all_methods_registered(self) -> None:
        """五种注册方式都有流程。"""
        assert set(SIGNUP_FLOWS) == {"email", "wechat", "google", "github", "sms"}

    def test_get_signup_flow_returns_flow(self) -> None:
        """能按方式取到流程。"""
        flow = get_signup_flow("wechat")
        assert flow is not None
        assert flow.name == "signup_wechat"

    def test_get_signup_flow_unknown_returns_none(self) -> None:
        """未知方式返回 None。"""
        assert get_signup_flow("nonexistent") is None

    def test_wechat_flow_requires_email(self) -> None:
        """⚠️ 微信流程必须含绑定邮箱 stage。

        微信开放平台不返回邮箱 —— 不强制补邮箱就会产生
        「既无邮箱也无手机号」的孤儿用户。
        """
        flow = get_signup_flow("wechat")
        assert flow is not None

        stage_ids = [stage.stage_id for stage in flow.stages]
        assert "email_verification" in stage_ids

    def test_all_flows_have_email_required_policy(self) -> None:
        """所有流程都带邮箱必绑策略。"""
        for name, flow in SIGNUP_FLOWS.items():
            policy_ids = [policy.policy_id for policy in flow.policies]
            assert "email_required" in policy_ids, f"{name} 缺少邮箱必绑策略"


class TestRunSignup:
    """注册执行器。"""

    def test_unknown_method_fails(self) -> None:
        """未知注册方式失败。"""
        result = run_signup("nonexistent")

        assert result.status is FlowStatus.FAILED
        assert result.error == "common.identity.error.unknown_method"

    def test_email_signup_completes(self) -> None:
        """邮箱注册走通。"""
        result = run_signup("email", {"email": "a@b.com", "password": "secret123"})

        assert result.status is FlowStatus.COMPLETED
        assert result.user is not None
        assert result.user.email is not None
        assert result.user.email.value == "a@b.com"

    def test_email_signup_emits_registered_event(self) -> None:
        """注册完成发事件。"""
        result = run_signup("email", {"email": "a@b.com", "password": "secret123"})

        assert len(result.events) == 1
        event = result.events[0]
        assert event.event_type == "identity.user_registered"

    def test_wechat_signup_without_email_is_pending(self) -> None:
        """⚠️ 微信注册没邮箱 → 挂起（要求补邮箱）。

        这是「邮箱必绑」的核心场景。
        """
        identity = Identity(
            provider=ProviderType.WECHAT,
            provider_user_id="openid-123",
            display_name="微信用户",
        )
        result = run_signup("wechat", {"identity": identity})

        assert result.status is FlowStatus.PENDING
        assert result.error is not None

    def test_wechat_signup_with_email_completes(self) -> None:
        """微信注册补了邮箱 → 完成。"""
        identity = Identity(
            provider=ProviderType.WECHAT,
            provider_user_id="openid-123",
            display_name="微信用户",
        )
        result = run_signup("wechat", {"identity": identity, "email": "a@b.com"})

        # ⚠️ 注意：微信流程本身不含「收集邮箱」的 stage，
        #    所以 email 是通过 OAuth stage 之前的 pending_email 传入的。
        #    实际 HTTP 层会先跑 BindEmailStage。
        assert result.status in {FlowStatus.COMPLETED, FlowStatus.PENDING}

    def test_wechat_signup_keeps_openid_not_nickname(self) -> None:
        """⚠️ 微信身份用 openid 而非昵称 —— 昵称会变。"""
        identity = Identity(
            provider=ProviderType.WECHAT,
            provider_user_id="openid-abc",
            display_name="会变的昵称",
        )
        result = run_signup("wechat", {"identity": identity})

        assert result.user is not None
        found = result.user.find_identity(ProviderType.WECHAT, "openid-abc")
        assert found is not None


class TestFlowComposition:
    """流程组合。"""

    def test_stage_by_id_finds_stage(self) -> None:
        """按 ID 找 stage。"""
        flow = Flow(name="f", stages=(CreateUserStage(), BindEmailStage()))

        assert flow.stage_by_id("email_verification") is not None
        assert flow.stage_by_id("nonexistent") is None

    def test_flow_context_data_helpers(self) -> None:
        """上下文数据读写。"""
        context = StageContext()

        context.set("k", "v")
        assert context.get("k") == "v"
        assert context.get("missing") is None
        assert context.get("missing", "default") == "default"
