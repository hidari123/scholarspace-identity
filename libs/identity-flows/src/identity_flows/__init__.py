"""scholarspace-identity-flows —— 流程引擎。

⚠️ 公开 API 只从这里导出。禁止 `from identity_flows.engine import ...`。
"""

from identity_flows.engine import (
    BindEmailStage,
    BindPhoneStage,
    CreateUserStage,
    Flow,
    FlowResult,
    FlowStatus,
    Stage,
    StageContext,
    StageError,
    StageResult,
    run_flow,
)
from identity_flows.flows import (
    SIGNUP_FLOWS,
    SignUpEmailStage,
    SignUpOAuthStage,
    SignUpPasswordStage,
    SignUpSmsStage,
    get_signup_flow,
)
from identity_flows.runner import continue_flow, run_signup

__version__ = "0.1.0"

__all__ = [
    "SIGNUP_FLOWS",
    "BindEmailStage",
    "BindPhoneStage",
    "CreateUserStage",
    "Flow",
    "FlowResult",
    "FlowStatus",
    "SignUpEmailStage",
    "SignUpOAuthStage",
    "SignUpPasswordStage",
    "SignUpSmsStage",
    "Stage",
    "StageContext",
    "StageError",
    "StageResult",
    "__version__",
    "continue_flow",
    "get_signup_flow",
    "run_flow",
    "run_signup",
]
