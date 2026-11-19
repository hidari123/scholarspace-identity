"""scholarspace-identity-core —— 身份领域核心。

⚠️ 纯领域包，**零运行时依赖**。
   这是本仓能被复用到任何项目的前提 —— 装它不需要拖进 FastAPI/SQLAlchemy。

   公开 API 只从这里导出。禁止 `from identity_core.entities import ...`。
"""

from identity_core.entities import (
    Credential,
    CredentialType,
    EmailAddress,
    Identity,
    InvalidEmailError,
    InvalidPhoneError,
    PhoneNumber,
    ProviderType,
    User,
)
from identity_core.events import (
    IdentityBound,
    IdentityEvent,
    UserEmailBound,
    UserLoggedIn,
    UserRegistered,
)
from identity_core.policy import (
    EmailRequiredPolicy,
    PhoneRequiredPolicy,
    Policy,
    PolicyAction,
    PolicyDecision,
    evaluate_policies,
)

__version__ = "0.1.0"

__all__ = [
    "Credential",
    "CredentialType",
    "EmailAddress",
    "EmailRequiredPolicy",
    "Identity",
    "IdentityBound",
    "IdentityEvent",
    "InvalidEmailError",
    "InvalidPhoneError",
    "PhoneNumber",
    "PhoneRequiredPolicy",
    "Policy",
    "PolicyAction",
    "PolicyDecision",
    "ProviderType",
    "User",
    "UserEmailBound",
    "UserLoggedIn",
    "UserRegistered",
    "__version__",
    "evaluate_policies",
]
