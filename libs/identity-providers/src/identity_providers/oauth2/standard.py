"""Google 与 GitHub 登录（标准 OAuth2）。

⚠️ 两者的共同点：
  · 标准 OAuth2 授权码流程
  · 都能拿到邮箱（scope 不同）
  · 用 `sub` / `id` 作为 provider_user_id（不是昵称！）

⚠️ 关键差异 —— 邮箱的可靠性：

| Provider | scope | 邮箱 | 是否已验证 |
|---|---|---|---|
| Google | `openid email profile` | 一定有 | ✅ Google 保证 |
| GitHub | `user:email` | 可能有 | ⚠️ 主邮箱可能未验证 |

GitHub 的坑：
  · `GET /user` 返回的 `email` **可能为 null**（用户设为私有）
  · `GET /user/emails` 返回**邮箱列表**，第一个 `primary=true` 的是主邮箱
  · 但主邮箱的 `verified` **可能是 false**

⚠️ 所以 GitHub 登录的用户也要走「邮箱必绑」策略 ——
   拿到未验证的邮箱时，要求用户再验证一次。
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

__all__ = [
    "GitHubProvider",
    "GoogleProvider",
    "OAuth2Config",
]

GOOGLE_AUTHORIZE_URL: Final = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL: Final = "https://oauth2.googleapis.com/token"  # noqa: S105
GOOGLE_USERINFO_URL: Final = "https://openidconnect.googleapis.com/v1/userinfo"

GITHUB_AUTHORIZE_URL: Final = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL: Final = "https://github.com/login/oauth/access_token"  # noqa: S105
GITHUB_USER_URL: Final = "https://api.github.com/user"
GITHUB_USER_EMAILS_URL: Final = "https://api.github.com/user/emails"


@dataclass(frozen=True, slots=True)
class OAuth2Config:
    """标准 OAuth2 Provider 配置。"""

    client_id: str
    client_secret: str
    redirect_uri: str
    authorize_url: str
    token_url: str
    userinfo_url: str
    scope: str
    #: state 签名密钥
    state_secret: str
    #: state 有效期（秒）
    state_ttl: int = 300
    #: 额外参数（如 GitHub 的 `allow_signup`）
    extra_authorize_params: dict[str, str] | None = None

    def __post_init__(self) -> None:
        """校验配置完整性。"""
        if not self.client_id:
            raise ValueError("client_id 未配置")
        if not self.client_secret:
            raise ValueError("client_secret 未配置")
        if not self.redirect_uri:
            raise ValueError("redirect_uri 未配置")
        if not self.state_secret:
            raise ValueError("state_secret 未配置（用于防 CSRF）")


@dataclass(frozen=True, slots=True)
class _BaseOAuth2Provider:
    """标准 OAuth2 Provider 基类。"""

    config: OAuth2Config
    provider_type: ProviderType
    redirect_uri: str = ""

    def __post_init__(self) -> None:
        """补齐 redirect_uri。"""
        if not self.redirect_uri:
            object.__setattr__(self, "redirect_uri", self.config.redirect_uri)

    @property
    def authorize_url(self) -> str:
        """授权端点。"""
        return self.config.authorize_url

    @property
    def _codec(self) -> OAuth2StateCodec:
        """state 编解码器。"""
        return OAuth2StateCodec(self.config.state_secret, self.config.state_ttl)

    def generate_state(self) -> str:
        """生成签名 state。"""
        return self._codec.generate()

    def verify_state(self, state: str, expected_state: str | None = None) -> bool:
        """校验 state。"""
        return self._codec.verify(state, expected_state)

    def build_authorize_url(self, state: str) -> str:
        """构造授权跳转 URL。"""
        params: dict[str, str] = {
            "client_id": self.config.client_id,
            "redirect_uri": self.config.redirect_uri,
            "response_type": "code",
            "scope": self.config.scope,
            "state": state,
        }
        if self.config.extra_authorize_params:
            params.update(self.config.extra_authorize_params)

        return f"{self.config.authorize_url}?{urlencode(params)}"

    async def exchange_code(self, code: str, state: str | None = None) -> OAuthProfile:
        """用 code 换取用户档案。"""
        if not code:
            raise InvalidCredentialError("缺少授权码")

        # ① 先校验 state（防 CSRF）
        if state is not None and not self.verify_state(state):
            raise InvalidCredentialError("state 校验失败")

        # ② code 换 token
        token_data = await self._request_token(code)

        # ③ 拿用户信息
        profile = await self._fetch_profile(token_data)

        return profile

    async def _request_token(self, code: str) -> dict[str, Any]:
        """换取 access_token。"""
        payload = {
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "code": code,
            "redirect_uri": self.config.redirect_uri,
            "grant_type": "authorization_code",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.config.token_url,
                    data=payload,
                    headers={"Accept": "application/json"},
                )
                data: dict[str, Any] = response.json()
        except Exception as error:
            raise ProviderError(f"换取 access_token 失败：{error}") from error

        if data.get("error"):
            raise InvalidCredentialError(str(data.get("error_description", data["error"])))

        return data

    async def _fetch_profile(self, token_data: dict[str, Any]) -> OAuthProfile:
        """取用户档案（子类实现）。"""
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class GoogleProvider(_BaseOAuth2Provider):
    """Google 登录。

    ⚠️ Google 用 OIDC —— `sub` 是稳定标识，邮箱由 Google 保证已验证。
    """

    provider_type: ProviderType = ProviderType.GOOGLE

    async def _fetch_profile(self, token_data: dict[str, Any]) -> OAuthProfile:
        """取用户档案。"""
        access_token = token_data.get("access_token")
        if not access_token:
            raise InvalidCredentialError("未获得 access_token")

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self.config.userinfo_url,
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                data: dict[str, Any] = response.json()
        except Exception as error:
            raise ProviderError(f"获取 Google 用户信息失败：{error}") from error

        # ⚠️ sub 才是稳定标识 —— email 可能变（用户换邮箱）
        subject = data.get("sub")
        if not subject:
            raise InvalidCredentialError("Google 未返回 sub")

        email = data.get("email")
        # ⚠️ Google 的 email_verified 可能是字符串 "true"
        email_verified = data.get("email_verified") in (True, "true")

        return OAuthProfile(
            provider=ProviderType.GOOGLE,
            provider_user_id=str(subject),
            display_name=data.get("name"),
            avatar_url=data.get("picture"),
            email=email,
            email_verified=email_verified,
            access_token=access_token,
            refresh_token=token_data.get("refresh_token"),
            expires_at=token_data.get("expires_in"),
            raw={"hd": data.get("hd")},
        )


@dataclass(frozen=True, slots=True)
class GitHubProvider(_BaseOAuth2Provider):
    """GitHub 登录。

    ⚠️ 邮箱的坑：
      · `GET /user` 的 email 可能为 null（用户设为私有）
      · 需要额外调 `GET /user/emails` 拿邮箱列表
      · 主邮箱（primary=true）可能**未验证**
    """

    provider_type: ProviderType = ProviderType.GITHUB

    async def _fetch_profile(self, token_data: dict[str, Any]) -> OAuthProfile:
        """取用户档案。"""
        access_token = token_data.get("access_token")
        if not access_token:
            raise InvalidCredentialError("未获得 access_token")

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                user_resp = await client.get(GITHUB_USER_URL, headers=headers)
                user_data = user_resp.json()

                # 邮箱可能要单独取
                emails_resp = await client.get(GITHUB_USER_EMAILS_URL, headers=headers)
                emails = emails_resp.json() if isinstance(emails_resp.json(), list) else []
        except Exception as error:
            raise ProviderError(f"获取 GitHub 用户信息失败：{error}") from error

        user_id = user_data.get("id")
        if not user_id:
            raise InvalidCredentialError("GitHub 未返回 id")

        email, email_verified = self._pick_email(user_data, emails)

        return OAuthProfile(
            provider=ProviderType.GITHUB,
            provider_user_id=str(user_id),
            display_name=user_data.get("name") or user_data.get("login"),
            avatar_url=user_data.get("avatar_url"),
            email=email,
            email_verified=email_verified,
            access_token=access_token,
            refresh_token=token_data.get("refresh_token"),
            expires_at=token_data.get("expires_in"),
            raw={"login": user_data.get("login"), "html_url": user_data.get("html_url")},
        )

    def _pick_email(
        self,
        user_data: dict[str, Any],
        emails: list[dict[str, Any]],
    ) -> tuple[str | None, bool]:
        """挑一个邮箱。

        优先级：
          1. emails 列表里 primary 且 verified 的
          2. emails 列表里第一个 verified 的
          3. emails 列表里第一个 primary 的（可能未验证）
          4. user_data.email（可能为 null 或未验证）

        ⚠️ 返回的 verified 可能是 False —— 这时「邮箱必绑」策略
           会要求用户再验证一次。
        """
        # ① primary + verified
        for entry in emails:
            if entry.get("primary") and entry.get("verified"):
                return str(entry.get("email")), True

        # ② 任意 verified
        for entry in emails:
            if entry.get("verified"):
                return str(entry.get("email")), True

        # ③ primary（未验证）
        for entry in emails:
            if entry.get("primary"):
                return str(entry.get("email")), False

        # ④ 用户信息里的 email
        fallback = user_data.get("email")
        if fallback:
            return str(fallback), False

        return None, False
