r"""微信开放平台（网站应用）登录。

⚠️ 微信开放平台的「网站应用」用的是 `snsapi_login` scope ——
   跟公众号网页授权（`snsapi_base` / `snsapi_userinfo`）**不是一回事**。

流程：
    1. 前端加载微信官方 WxLogin JS SDK，渲染二维码
    2. 用户扫码 → 微信回调 redirect_uri，带回 code + state
    3. 后端校验 state（防 CSRF）→ 用 code 换 access_token
    4. 用 access_token + openid 调 sns/userinfo 拿昵称头像

⚠️⚠️ **微信不返回邮箱** —— 这是「邮箱必绑」策略的现实来源。

---

## 与 scholar-club 旧实现的差异（旧实现有安全漏洞）

| # | 问题 | 旧实现 | 本实现 |
|---|---|---|---|
| 1 | **state 未校验** | 前端生成 `state` 但后端从不校验 → **CSRF 漏洞** | 服务端生成 + 签名，强制校验 |
| 2 | JWT 密钥硬编码兜底 | `JWT_SECRET \|\| 'your-jwt-secret-key'` | 无兜底，缺失即启动失败 |
| 3 | 打印 access_token | `access_token.substring(0, 20)` | **不记日志** |
| 4 | redirect_uri 写死 | 硬编码在代码里 | 按环境配置 |
| 5 | AppID 前端兜底 | 前端有默认值 `wxaad97523e6cc15f2` | 只存服务端，前端无兜底 |

---

## 微信接口返回的错误码

`errcode` 不为 0 时 `errmsg` 有值。常见的：

| errcode | 含义 | 处理 |
|---|---|---|
| 40029 | code 无效 | 提示重新扫码 |
| 40163 | code 已被使用 | 提示重新扫码（**不要重试**）|
| 45011 | API 调用频率限制 | 稍后重试 |
| 40226 | 跨域被禁 | 需在微信后台配置域名 |
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final
from urllib.parse import urlencode

import httpx
from identity_core.entities import ProviderType

from identity_providers.base import (
    InvalidCredentialError,
    OAuthProfile,
    ProviderError,
)
from identity_providers.oauth2.state import OAuth2StateCodec

__all__ = ["WechatConfig", "WechatOAuthError", "WechatProvider"]

#: 微信开放平台授权端点
WECHAT_AUTHORIZE_URL: Final = "https://open.weixin.qq.com/connect/qrconnect"
#: 换取 access_token
WECHAT_ACCESS_TOKEN_URL: Final = "https://api.weixin.qq.com/sns/oauth2/access_token"  # noqa: S105
#: 取用户信息
WECHAT_USERINFO_URL: Final = "https://api.weixin.qq.com/sns/userinfo"


class WechatOAuthError(ProviderError):
    """微信返回了错误。"""

    def __init__(self, errcode: int, errmsg: str) -> None:
        """初始化。"""
        super().__init__(f"微信错误 {errcode}: {errmsg}")
        self.errcode = errcode
        self.errmsg = errmsg


@dataclass(frozen=True, slots=True)
class WechatConfig:
    """微信开放平台配置。"""

    appid: str
    secret: str
    redirect_uri: str
    #: state 签名密钥 —— 用于防 CSRF
    state_secret: str
    #: 授权 scope —— 网站应用固定 snsapi_login
    scope: str = "snsapi_login"
    #: 授权页样式
    style: str = "black"
    #: state 有效期（秒）—— 超过即失效
    state_ttl: int = 300

    def __post_init__(self) -> None:
        """校验配置完整性。

        ⚠️ 刻意**没有**默认值兜底 —— 旧实现里
           `JWT_SECRET || 'your-jwt-secret-key'` 这种兜底
           会让「忘记配置」变成「上线即泄露」。
        """
        if not self.appid:
            raise ValueError("微信 appid 未配置")
        if not self.secret:
            raise ValueError("微信 secret 未配置")
        if not self.redirect_uri:
            raise ValueError("微信 redirect_uri 未配置")
        if not self.state_secret:
            raise ValueError("微信 state_secret 未配置（用于防 CSRF）")


@dataclass(frozen=True, slots=True)
class WechatProvider:
    """微信开放平台（网站应用）Provider。"""

    config: WechatConfig
    provider_type: ProviderType = ProviderType.WECHAT
    authorize_url: str = WECHAT_AUTHORIZE_URL
    redirect_uri: str = ""

    def __post_init__(self) -> None:
        """补齐 redirect_uri。"""
        if not self.redirect_uri:
            object.__setattr__(self, "redirect_uri", self.config.redirect_uri)

    # ── state 生成与校验（防 CSRF）──────────────────────────

    def generate_state(self) -> str:
        """生成签名 state。

        ⚠️ state 必须由**服务端**生成并签名 ——
           客户端生成的 state 服务端无法校验（客户端被攻破即可伪造）。

        格式：`<随机串>.<过期时间戳>.<HMAC签名>`
        """
        return self._codec.generate()

    def verify_state(self, state: str, expected_state: str | None = None) -> bool:
        """校验 state。

        校验三件事：
          ① 签名匹配（防止客户端伪造）
          ② 未过期（防止重放旧的）
          ③ 若调用方提供了 expected_state，则必须一致

        Args:
            state: 微信回调带回的 state
            expected_state: 会话里存的状态（单会话模式）

        Returns:
            是否有效
        """
        # ⚠️ 用共享的 OAuth2StateCodec —— 微信/Google/GitHub 行为必须完全一致
        return self._codec.verify(state, expected_state)

    @property
    def _codec(self) -> OAuth2StateCodec:
        """state 编解码器（共享实现）。"""
        return OAuth2StateCodec(self.config.state_secret, self.config.state_ttl)

    # ── OAuth2 流程 ─────────────────────────────────────────

    def build_authorize_url(self, state: str) -> str:
        """构造扫码授权 URL。

        ⚠️ 微信的 URL 用 `#wechat_redirect` 结尾 —— 这是微信的硬性要求，
           少了会白屏。
        """
        params = {
            "appid": self.config.appid,
            "redirect_uri": self.config.redirect_uri,
            "response_type": "code",
            "scope": self.config.scope,
            "state": state,
            "style": self.config.style,
            "href": "",
        }
        query = urlencode(params)
        return f"{self.authorize_url}?{query}#wechat_redirect"

    async def exchange_code(self, code: str, state: str | None = None) -> OAuthProfile:
        """用 code 换取用户档案。

        Args:
            code: 微信回调带来的授权码
            state: 回传的 state（若提供则校验）

        Raises:
            InvalidCredentialError: state 不匹配 / code 无效
            WechatOAuthError: 微信返回错误
            ProviderError: 网络异常
        """
        if not code:
            raise InvalidCredentialError("缺少授权码")

        # ① 先校验 state（防 CSRF）—— 在用 code 之前
        if state is not None and not self.verify_state(state):
            raise InvalidCredentialError("state 校验失败")

        # ② code 换 access_token
        token_data = await self._request_token(code)

        access_token = token_data.get("access_token")
        openid = token_data.get("openid")
        if not access_token or not openid:
            raise InvalidCredentialError("微信未返回 access_token/openid")

        # ③ 取用户信息（昵称 + 头像）
        user_info = await self._request_userinfo(access_token, openid)

        # ⚠️ 微信不返回邮箱 —— email 保持 None
        #    「邮箱必绑」由 EmailRequiredPolicy 强制补齐
        return OAuthProfile(
            provider=ProviderType.WECHAT,
            provider_user_id=openid,
            display_name=user_info.get("nickname"),
            avatar_url=user_info.get("headimgurl"),
            email=None,
            email_verified=False,
            access_token=access_token,
            refresh_token=token_data.get("refresh_token"),
            expires_at=token_data.get("expires_in"),
            raw={"unionid": token_data.get("unionid"), "sex": user_info.get("sex")},
        )

    async def _request_token(self, code: str) -> dict[str, Any]:
        """换取 access_token。"""
        params = {
            "appid": self.config.appid,
            "secret": self.config.secret,
            "code": code,
            "grant_type": "authorization_code",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(WECHAT_ACCESS_TOKEN_URL, params=params)
                data: dict[str, Any] = response.json()
        except Exception as error:
            raise ProviderError(f"调用微信接口失败：{error}") from error

        errcode = data.get("errcode")
        if errcode:
            raise WechatOAuthError(int(errcode), str(data.get("errmsg", "unknown")))

        return data

    async def _request_userinfo(self, access_token: str, openid: str) -> dict[str, Any]:
        """取用户信息。

        ⚠️ **access_token 不写日志** —— 旧实现打了前 20 字符，那是凭证泄露。
        """
        params = {"access_token": access_token, "openid": openid}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(WECHAT_USERINFO_URL, params=params)
                data: dict[str, Any] = response.json()
        except Exception as error:
            raise ProviderError(f"调用微信用户信息接口失败：{error}") from error

        errcode = data.get("errcode")
        if errcode:
            raise WechatOAuthError(int(errcode), str(data.get("errmsg", "unknown")))

        return data
