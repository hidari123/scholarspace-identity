"""Stage 引擎 —— 借鉴 authentik 的 stage 架构思想。

⚠️ 设计：**登录注册是一串可配置步骤**，不是硬编码的 if-else。

    Flow(
        name='signup_wechat',
        stages=[WechatOAuthStage, BindEmailStage, CreateUserStage],
        policies=[EmailRequiredPolicy],
    )

每个 Stage：
  · 有唯一 stage_id
  · 声明自己能否在**无用户**的上下文中运行
  · 产出对 context 的修改

Policy 在每个 Stage 之后评估：
  · 要求某个 Stage → 跳到那个 Stage
  · 拒绝 → 流程失败

这借鉴 authentik 的 stage/policy 机制，**实现完全自研**。
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import StrEnum
from typing import Any, ClassVar, Protocol, runtime_checkable

from identity_core.entities import EmailAddress, PhoneNumber, User
from identity_core.policy import Policy, PolicyDecision, evaluate_policies

__all__ = [
    "Flow",
    "FlowResult",
    "FlowStatus",
    "Stage",
    "StageContext",
    "StageError",
    "StageResult",
    "run_flow",
]


class StageError(Exception):
    """Stage 执行失败。"""


class FlowStatus(StrEnum):
    """流程状态。"""

    #: 全部完成
    COMPLETED = "completed"
    #: 需要用户补充信息（挂起，等用户回来）
    PENDING = "pending"
    #: 失败
    FAILED = "failed"
    #: 被策略拒绝
    DENIED = "denied"


@dataclass(slots=True)
class StageContext:
    """Stage 之间的传递上下文。

    ⚠️ 这不是领域对象 —— 它是流程的**可变状态**。
       领域对象（User 等）仍然不可变。
    """

    #: 当前用户（可能为 None）
    user: User | None = None

    #: 流程收集到的数据（stage 之间传递）
    data: dict[str, Any] = field(default_factory=dict)

    #: 待创建的邮箱（等待验证）
    pending_email: str | None = None

    #: 待创建的手机号
    pending_phone: str | None = None

    #: 流程产生的领域事件
    events: list[Any] = field(default_factory=list)

    #: 错误信息（i18n key）
    error: str | None = None

    def set(self, key: str, value: Any) -> None:
        """设置数据项。"""
        self.data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """读取数据项。"""
        return self.data.get(key, default)


@dataclass(frozen=True, slots=True)
class StageResult:
    """Stage 执行结果。"""

    #: 是否成功
    ok: bool
    #: 挂起原因（需要用户补充信息）
    pending_reason: str | None = None
    #: 错误信息（i18n key）
    error: str | None = None


@runtime_checkable
class Stage(Protocol):
    """Stage 协议。

    实现类需要提供 `stage_id` 与 `run`。

    ⚠️ `stage_id` / `allows_anonymous` 用 `ClassVar` 声明 ——
       实现类是 `@dataclass(frozen=True, slots=True)`，这两个字段是
       **类级常量**（每个 stage 类型固定），不是实例状态。
       若在 Protocol 里声明为普通实例属性，mypy 会认为
       dataclass 的类级默认值不满足协议 → 报 arg-type 不兼容。
    """

    #: Stage 唯一标识
    stage_id: ClassVar[str]

    #: 是否可以在「还没有用户」时运行（如注册的第一步）
    allows_anonymous: ClassVar[bool]

    def run(self, context: StageContext) -> StageResult:
        """执行。

        Args:
            context: 流程上下文（可变，就地修改）

        Returns:
            执行结果
        """
        ...


@dataclass(frozen=True, slots=True)
class Flow:
    """流程定义。"""

    #: 流程名
    name: str

    #: Stage 序列
    stages: tuple[Stage, ...]

    #: 策略序列（按顺序短路评估）
    policies: tuple[Policy, ...] = ()

    #: 失败/拒绝时用的 i18n key 前缀
    error_prefix: str = "common.identity.error"

    def stage_by_id(self, stage_id: str) -> Stage | None:
        """按 ID 找 Stage。"""
        for stage in self.stages:
            if stage.stage_id == stage_id:
                return stage
        return None


@dataclass(frozen=True, slots=True)
class FlowResult:
    """流程执行结果。"""

    status: FlowStatus
    user: User | None = None
    context: StageContext | None = None
    error: str | None = None

    @property
    def ok(self) -> bool:
        """是否成功。"""
        return self.status is FlowStatus.COMPLETED

    @property
    def events(self) -> list[Any]:
        """产生的事件。"""
        return self.context.events if self.context else []


def run_flow(flow: Flow, context: StageContext) -> FlowResult:
    """执行流程（内部）。

    算法：
      1. 依次跑每个 Stage
      2. 每跑完一个 Stage，评估策略
         - 要求某 Stage → 跳到那个 Stage（若已在流程里）
         - 拒绝 → 返回 DENIED
      3. 全部 Stage 跑完 → COMPLETED
    """
    # 记录已跑过的 stage，避免策略反复要求同一个 stage 造成死循环
    executed: set[str] = set()
    index = 0

    while index < len(flow.stages):
        stage = flow.stages[index]

        # 同一个 stage 不重复跑（策略可能又要求它）
        if stage.stage_id in executed:
            index += 1
            continue

        if context.user is None and not stage.allows_anonymous:
            return FlowResult(
                status=FlowStatus.FAILED,
                context=context,
                error=f"{flow.error_prefix}.stage_requires_user",
            )

        result = stage.run(context)

        if not result.ok:
            if result.pending_reason is not None:
                return FlowResult(
                    status=FlowStatus.PENDING,
                    user=context.user,
                    context=context,
                    error=result.pending_reason,
                )
            return FlowResult(
                status=FlowStatus.FAILED,
                user=context.user,
                context=context,
                error=result.error or f"{flow.error_prefix}.unknown",
            )

        executed.add(stage.stage_id)

        # ── 策略评估 ────────────────────────────────────
        decision: PolicyDecision = evaluate_policies(list(flow.policies), context.user)

        if decision.action.value == "deny":
            return FlowResult(
                status=FlowStatus.DENIED,
                user=context.user,
                context=context,
                error=decision.reason or f"{flow.error_prefix}.denied",
            )

        if decision.action.value == "require_stage":
            target = flow.stage_by_id(decision.stage or "")
            if target is None:
                return FlowResult(
                    status=FlowStatus.FAILED,
                    user=context.user,
                    context=context,
                    error=f"{flow.error_prefix}.unknown_stage",
                )

            # ── 跳到策略要求的 Stage ──────────────────────
            #
            # ⚠️ 关键：不能重置 executed。
            #    若重置，被跳过的 stage（如 BindEmailStage）会再跑一遍，
            #    而它此时 pending_email 已被清空 → 永远返回 pending → 死循环。
            #
            #    正确做法：把目标 stage **前插**到剩余队列最前面，
            #    保留已执行记录。
            remaining = list(flow.stages[index + 1 :])
            flow = replace(flow, stages=(target, *remaining))
            index = 0
            continue

        index += 1

    return FlowResult(status=FlowStatus.COMPLETED, user=context.user, context=context)


# ══════════════════════════════════════════════════════════
# 内置 Stage
# ══════════════════════════════════════════════════════════


@dataclass(frozen=True, slots=True)
class BindEmailStage:
    """绑定邮箱。

    ⚠️ 微信注册必经 —— 微信不返回邮箱。
    """

    stage_id: ClassVar[str] = "email_verification"
    allows_anonymous: ClassVar[bool] = True

    def run(self, context: StageContext) -> StageResult:
        """执行。"""
        email = context.pending_email
        if not email:
            return StageResult(
                ok=False,
                pending_reason="common.identity.error.email_required",
            )

        try:
            address = EmailAddress(email)
        except ValueError:
            return StageResult(ok=False, error="common.identity.error.invalid_email")

        if context.user is None:
            context.user = User.create(email=address)
        else:
            context.user = context.user.with_email(address)

        context.pending_email = None
        return StageResult(ok=True)


@dataclass(frozen=True, slots=True)
class BindPhoneStage:
    """绑定手机号。"""

    stage_id: ClassVar[str] = "sms_verification"
    allows_anonymous: ClassVar[bool] = True

    def run(self, context: StageContext) -> StageResult:
        """执行。"""
        phone = context.pending_phone
        if not phone:
            return StageResult(
                ok=False,
                pending_reason="common.identity.error.phone_required",
            )

        try:
            number = PhoneNumber(phone)
        except ValueError:
            return StageResult(ok=False, error="common.identity.error.invalid_phone")

        if context.user is None:
            context.user = User.create(phone=number)
        else:
            context.user = context.user.with_phone(number)

        context.pending_phone = None
        return StageResult(ok=True)


@dataclass(frozen=True, slots=True)
class CreateUserStage:
    """创建用户。

    ⚠️ 若上游已建用户（如 BindEmailStage），则复用。
    """

    stage_id: ClassVar[str] = "create_user"
    allows_anonymous: ClassVar[bool] = True

    def run(self, context: StageContext) -> StageResult:
        """执行。"""
        if context.user is None:
            context.user = User.create()
        return StageResult(ok=True)
