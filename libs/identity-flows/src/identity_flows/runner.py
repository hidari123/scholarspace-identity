"""流程执行器 —— 对外的统一入口。"""

from __future__ import annotations

from identity_core.entities import User
from identity_core.events import UserRegistered

from identity_flows.engine import Flow, FlowResult, FlowStatus, StageContext
from identity_flows.flows import get_signup_flow

__all__ = ["FlowStatus", "continue_flow", "run_signup"]


def _emit_registered_event(context: StageContext, user: User) -> None:
    """发注册完成事件。

    ⚠️ identity 只发事件 —— 不知道 billing / community 的存在。
    """
    context.events.append(
        UserRegistered(
            user_id=user.user_id,
            email=user.email.value if user.email else None,
            phone=user.phone.value if user.phone else None,
            display_name=user.display_name,
            providers=tuple(str(provider) for provider in user.providers),
            tenant_id=user.tenant_id,
        )
    )


def run_signup(
    method: str,
    data: dict[str, object] | None = None,
) -> FlowResult:
    """执行注册流程。

    Args:
        method: 注册方式（email / wechat / google / github / sms）
        data: 流程初始数据（如 `{"email": "...", "password": "..."}`）

    Returns:
        流程结果
    """
    flow = get_signup_flow(method)
    if flow is None:
        context = StageContext()
        error = "common.identity.error.unknown_method"
        context.error = error
        return FlowResult(status=FlowStatus.FAILED, context=context, error=error)

    context = StageContext(data=dict(data or {}))
    result = _execute(flow, context)

    if result.status is FlowStatus.COMPLETED and result.user is not None:
        _emit_registered_event(context, result.user)

    return result


def continue_flow(
    flow: Flow,
    context: StageContext,
) -> FlowResult:
    """继续一个挂起的流程。

    ⚠️ 用于「用户补邮箱后继续注册」这类场景 ——
       流程状态存在外部（session / redis），这里只负责继续跑。
    """
    result = _execute(flow, context)

    if result.status is FlowStatus.COMPLETED and result.user is not None:
        _emit_registered_event(context, result.user)

    return result


def _execute(flow: Flow, context: StageContext) -> FlowResult:
    """执行流程（内部）。

    ⚠️ 延迟 import 是为了避免 engine ↔ runner 的循环依赖：
       engine 定义流程原语，runner 定义对外入口。
       两者互相 import 会在模块初始化时拿到未定义的符号。
    """
    from identity_flows.engine import run_flow  # noqa: PLC0415

    return run_flow(flow, context)
