"""具体流程定义 —— 各注册方式的登录注册流程。

⚠️ 关键：**微信注册必须补邮箱**。

    微信开放平台的 `sns/userinfo` 接口不返回邮箱，
    所以微信注册的用户如果直接放行，平台上就会有一批
    「既没有邮箱也没有手机号」的用户 —— 无法联系、无法找回密码。

    这正是「邮箱必绑」策略的现实来源。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from identity_core.entities import User
from identity_core.policy import EmailRequiredPolicy, PhoneRequiredPolicy

from identity_flows.engine import (
    BindEmailStage,
    BindPhoneStage,
    CreateUserStage,
    Flow,
    StageContext,
    StageResult,
)

__all__ = [
    "SIGNUP_FLOWS",
    "SignUpEmailStage",
    "SignUpOAuthStage",
    "SignUpPasswordStage",
    "SignUpSmsStage",
    "get_signup_flow",
]


@dataclass(frozen=True, slots=True)
class SignUpEmailStage:
    """收集邮箱。

    ⚠️ 只收集，不验证 —— 验证由邮箱验证码 stage 完成。
    """

    stage_id: ClassVar[str] = "identify_email"
    allows_anonymous: ClassVar[bool] = True

    def run(self, context: StageContext) -> StageResult:
        """执行。"""
        email = context.get("email")
        if not email:
            return StageResult(
                ok=False,
                pending_reason="common.identity.error.email_required",
            )

        context.pending_email = str(email)
        return StageResult(ok=True)


@dataclass(frozen=True, slots=True)
class SignUpPasswordStage:
    """设置密码。

    ⚠️ 密码哈希由 infrastructure 层的 hasher 完成 ——
       领域层不碰具体算法。
    """

    stage_id: ClassVar[str] = "set_password"
    allows_anonymous: ClassVar[bool] = True

    def run(self, context: StageContext) -> StageResult:
        """执行。"""
        password = context.get("password")
        if not password:
            return StageResult(
                ok=False,
                pending_reason="common.identity.error.password_required",
            )

        context.set("password", password)
        return StageResult(ok=True)


@dataclass(frozen=True, slots=True)
class SignUpOAuthStage:
    """第三方 OAuth 登录。

    ⚠️ 上游 provider 已完成授权与回调换 token，
       这里只把结果放进 context。
    """

    stage_id: ClassVar[str] = "oauth"
    allows_anonymous: ClassVar[bool] = True

    def run(self, context: StageContext) -> StageResult:
        """执行。"""
        identity = context.get("identity")
        if not identity:
            return StageResult(
                ok=False,
                pending_reason="common.identity.error.oauth_pending",
            )

        # 已有用户 → 直接绑身份；没有 → 先建用户再绑
        user = context.user
        if user is None:
            user = User.create(
                display_name=getattr(identity, "display_name", None),
                avatar_url=getattr(identity, "avatar_url", None),
            )

        context.user = user.with_identity(identity)
        return StageResult(ok=True)


@dataclass(frozen=True, slots=True)
class SignUpSmsStage:
    """收集手机号。

    ⚠️ 短信验证码的发送与校验由 infrastructure 层完成。
    """

    stage_id: ClassVar[str] = "identify_phone"
    allows_anonymous: ClassVar[bool] = True

    def run(self, context: StageContext) -> StageResult:
        """执行。"""
        phone = context.get("phone")
        if not phone:
            return StageResult(
                ok=False,
                pending_reason="common.identity.error.phone_required",
            )

        context.pending_phone = str(phone)
        return StageResult(ok=True)


# ══════════════════════════════════════════════════════════
# 流程定义
# ══════════════════════════════════════════════════════════

#: 邮箱注册 —— 邮箱 + 密码
_SIGNUP_EMAIL = Flow(
    name="signup_email",
    stages=(
        SignUpEmailStage(),
        SignUpPasswordStage(),
        BindEmailStage(),
        CreateUserStage(),
    ),
    policies=(EmailRequiredPolicy(),),
)

#: 微信注册 —— ⚠️ 必须补邮箱（微信不给邮箱）
_SIGNUP_WECHAT = Flow(
    name="signup_wechat",
    stages=(
        SignUpOAuthStage(),
        BindEmailStage(),
        CreateUserStage(),
    ),
    policies=(EmailRequiredPolicy(),),
)

#: Google 注册 —— OAuth2 提供邮箱
_SIGNUP_GOOGLE = Flow(
    name="signup_google",
    stages=(
        SignUpOAuthStage(),
        BindEmailStage(),
        CreateUserStage(),
    ),
    policies=(EmailRequiredPolicy(),),
)

#: GitHub 注册 —— OAuth2 可能不给邮箱（主邮箱未验证时）
_SIGNUP_GITHUB = Flow(
    name="signup_github",
    stages=(
        SignUpOAuthStage(),
        BindEmailStage(),
        CreateUserStage(),
    ),
    policies=(EmailRequiredPolicy(),),
)

#: 手机号注册 —— 需要手机号 + 短信验证
_SIGNUP_SMS = Flow(
    name="signup_sms",
    stages=(
        SignUpSmsStage(),
        BindPhoneStage(),
        CreateUserStage(),
    ),
    policies=(EmailRequiredPolicy(), PhoneRequiredPolicy()),
)

#: 全部注册流程
SIGNUP_FLOWS: dict[str, Flow] = {
    "email": _SIGNUP_EMAIL,
    "wechat": _SIGNUP_WECHAT,
    "google": _SIGNUP_GOOGLE,
    "github": _SIGNUP_GITHUB,
    "sms": _SIGNUP_SMS,
}


def get_signup_flow(method: str) -> Flow | None:
    """按注册方式取流程。"""
    return SIGNUP_FLOWS.get(method)
