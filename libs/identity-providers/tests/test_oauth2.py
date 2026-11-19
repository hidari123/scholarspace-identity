"""OAuth2 Provider 测试 —— 重点验证防 CSRF 的 state 机制。"""

from __future__ import annotations

import asyncio

import pytest
from identity_core.entities import ProviderType

from identity_providers import (
    GitHubProvider,
    GoogleProvider,
    OAuth2Config,
    OAuth2StateCodec,
    WechatConfig,
    WechatOAuthError,
    WechatProvider,
)


def make_wechat_config(**overrides: object) -> WechatConfig:
    """造一个微信配置。"""
    defaults: dict[str, object] = {
        "appid": "wxtest123",
        "secret": "secret456",
        "redirect_uri": "https://scholar.example.com/api/identity/wechat/callback",
        "state_secret": "state-secret-xyz",
        "state_ttl": 300,
    }
    defaults.update(overrides)
    return WechatConfig(**defaults)  # type: ignore[arg-type]


class TestWechatConfig:
    """微信配置。"""

    def test_requires_appid(self) -> None:
        """appid 必填。"""
        with pytest.raises(ValueError, match="appid"):
            make_wechat_config(appid="")

    def test_requires_secret(self) -> None:
        """secret 必填。"""
        with pytest.raises(ValueError, match="secret"):
            make_wechat_config(secret="")

    def test_requires_redirect_uri(self) -> None:
        """redirect_uri 必填 —— 不硬编码。"""
        with pytest.raises(ValueError, match="redirect_uri"):
            make_wechat_config(redirect_uri="")

    def test_requires_state_secret(self) -> None:
        """state_secret 必填 —— 没有它就没有 CSRF 防护。"""
        with pytest.raises(ValueError, match="state_secret"):
            make_wechat_config(state_secret="")

    def test_has_no_secret_fallback(self) -> None:
        """⚠️ 刻意没有「默认 secret」兜底。

        旧实现的 `JWT_SECRET || 'your-jwt-secret-key'` 会让
        「忘记配置」变成「上线即泄露」。
        """
        with pytest.raises(ValueError):
            make_wechat_config(secret="")


class TestWechatState:
    """微信 state 生成与校验（防 CSRF）。"""

    def test_generated_state_verifies(self) -> None:
        """生成的 state 能通过校验。"""
        provider = WechatProvider(config=make_wechat_config())
        state = provider.generate_state()

        assert provider.verify_state(state) is True

    def test_state_has_three_parts(self) -> None:
        """state 格式为 <nonce>.<expires>.<sig>。"""
        provider = WechatProvider(config=make_wechat_config())
        state = provider.generate_state()

        assert len(state.split(".")) == 3

    def test_tampered_state_rejected(self) -> None:
        """⚠️ 篡改 state 会被拒。"""
        provider = WechatProvider(config=make_wechat_config())
        state = provider.generate_state()

        nonce, expires, signature = state.split(".")
        tampered = f"{nonce}.{expires}.{'0' * len(signature)}"

        assert provider.verify_state(tampered) is False

    def test_forged_state_rejected(self) -> None:
        """⚠️ 完全伪造的 state 会被拒（签名不匹配）。"""
        provider = WechatProvider(config=make_wechat_config())

        assert provider.verify_state("fake.nonce.alsosig") is False

    def test_empty_state_rejected(self) -> None:
        """空 state 被拒。"""
        provider = WechatProvider(config=make_wechat_config())

        assert provider.verify_state("") is False

    def test_malformed_state_rejected(self) -> None:
        """格式不对的 state 被拒。"""
        provider = WechatProvider(config=make_wechat_config())

        assert provider.verify_state("only-one-part") is False
        assert provider.verify_state("a.b") is False
        assert provider.verify_state("a.b.c.d") is False

    def test_expired_state_rejected(self) -> None:
        """⚠️ 过期 state 被拒（防重放）。"""
        provider = WechatProvider(config=make_wechat_config(state_ttl=-1))
        state = provider.generate_state()

        # ttl=-1 → 生成的 state 已经过期
        assert provider.verify_state(state) is False

    def test_state_signed_by_other_secret_rejected(self) -> None:
        """⚠️ 用别的密钥签的 state 被拒。"""
        real = WechatProvider(config=make_wechat_config())
        other = WechatProvider(
            config=make_wechat_config(state_secret="different-secret")  # noqa: S106
        )

        state = real.generate_state()

        assert other.verify_state(state) is False

    def test_expected_state_must_match(self) -> None:
        """⚠️ 与会话中 state 不一致时被拒（防跨会话重放）。"""
        provider = WechatProvider(config=make_wechat_config())
        state = provider.generate_state()

        # 会话里存的是别的 state
        assert provider.verify_state(state, expected_state="other.state.value") is False

    def test_expected_state_match_passes(self) -> None:
        """与会话中 state 一致时通过。"""
        provider = WechatProvider(config=make_wechat_config())
        state = provider.generate_state()

        assert provider.verify_state(state, expected_state=state) is True

    def test_states_are_unique(self) -> None:
        """每次生成的 state 不同（防重放）。"""
        provider = WechatProvider(config=make_wechat_config())

        states = {provider.generate_state() for _ in range(20)}

        assert len(states) == 20


class TestWechatAuthorizeUrl:
    """微信授权 URL。"""

    def test_contains_required_params(self) -> None:
        """包含必需参数。"""
        provider = WechatProvider(config=make_wechat_config())
        url = provider.build_authorize_url("state-123")

        assert "appid=wxtest123" in url
        assert "scope=snsapi_login" in url
        assert "state=state-123" in url
        assert "response_type=code" in url

    def test_ends_with_wechat_redirect(self) -> None:
        """⚠️ 必须以 #wechat_redirect 结尾 —— 少了微信会白屏。"""
        provider = WechatProvider(config=make_wechat_config())
        url = provider.build_authorize_url("state-123")

        assert url.endswith("#wechat_redirect")

    def test_uses_configured_redirect_uri(self) -> None:
        """用配置的 redirect_uri —— 不硬编码。"""
        provider = WechatProvider(config=make_wechat_config())
        url = provider.build_authorize_url("state-123")

        assert "redirect_uri=" in url
        assert "scholar.example.com" in url


class TestOAuth2StateCodec:
    """通用 state 编解码。"""

    def test_generate_and_verify(self) -> None:
        """生成 → 校验通过。"""
        codec = OAuth2StateCodec("secret")
        state = codec.generate()

        assert codec.verify(state) is True

    def test_reject_tampered(self) -> None:
        """篡改被拒。"""
        codec = OAuth2StateCodec("secret")
        state = codec.generate()

        nonce, expires, _ = state.split(".")
        assert codec.verify(f"{nonce}.{expires}.bad") is False

    def test_reject_expired(self) -> None:
        """过期被拒。"""
        codec = OAuth2StateCodec("secret", ttl=-1)
        state = codec.generate()

        assert codec.verify(state) is False

    def test_reject_wrong_secret(self) -> None:
        """换密钥后校验失败。"""
        state = OAuth2StateCodec("secret").generate()

        assert OAuth2StateCodec("other").verify(state) is False

    def test_reject_empty(self) -> None:
        """空值被拒。"""
        assert OAuth2StateCodec("secret").verify("") is False

    def test_requires_secret(self) -> None:
        """密钥不能为空。"""
        with pytest.raises(ValueError):
            OAuth2StateCodec("")


class TestStandardOAuth2:
    """Google / GitHub。"""

    def make_config(self, **overrides: object) -> OAuth2Config:
        """造一个 OAuth2 配置。"""
        defaults: dict[str, object] = {
            "client_id": "client-123",
            "client_secret": "secret-456",
            "redirect_uri": "https://scholar.example.com/callback",
            "authorize_url": "https://example.com/authorize",
            "token_url": "https://example.com/token",
            "userinfo_url": "https://example.com/userinfo",
            "scope": "openid email profile",
            "state_secret": "state-secret",
        }
        defaults.update(overrides)
        return OAuth2Config(**defaults)  # type: ignore[arg-type]

    def test_google_authorize_url(self) -> None:
        """Google 授权 URL。"""
        provider = GoogleProvider(config=self.make_config())

        url = provider.build_authorize_url("state-1")

        assert "client_id=client-123" in url
        assert "state=state-1" in url
        assert "scope=" in url

    def test_github_authorize_url(self) -> None:
        """GitHub 授权 URL。"""
        provider = GitHubProvider(
            config=self.make_config(
                authorize_url="https://github.com/login/oauth/authorize",
                scope="read:user user:email",
                extra_authorize_params={"allow_signup": "true"},
            )
        )

        url = provider.build_authorize_url("state-1")

        assert "github.com" in url
        assert "allow_signup=true" in url

    def test_provider_types(self) -> None:
        """Provider 类型正确。"""
        assert GoogleProvider(config=self.make_config()).provider_type is ProviderType.GOOGLE
        assert GitHubProvider(config=self.make_config()).provider_type is ProviderType.GITHUB

    def test_state_verified_before_token_exchange(self) -> None:
        """⚠️ state 校验发生在换取 token **之前**。

        这很重要 —— 校验失败就不该消耗 code。
        """
        provider = GoogleProvider(config=self.make_config())

        # 错误的 state → 在调用第三方之前就失败
        with pytest.raises(Exception) as info:
            asyncio.run(provider.exchange_code("some-code", state="forged.state.value"))

        assert "state" in str(info.value).lower()

    def test_requires_state_secret(self) -> None:
        """state_secret 必填。"""
        with pytest.raises(ValueError, match="state_secret"):
            self.make_config(state_secret="")

    def test_github_email_pick_prefers_verified_primary(self) -> None:
        """⚠️ GitHub 优先取「主邮箱且已验证」。"""
        provider = GitHubProvider(config=self.make_config())

        emails = [
            {"email": "unverified@example.com", "primary": True, "verified": False},
            {"email": "verified@example.com", "primary": False, "verified": True},
        ]

        email, verified = provider._pick_email({"email": "unverified@example.com"}, emails)

        assert email == "verified@example.com"
        assert verified is True

    def test_github_email_pick_falls_back_to_primary_unverified(self) -> None:
        """没有已验证邮箱时取主邮箱（未验证）。"""
        provider = GitHubProvider(config=self.make_config())

        emails = [{"email": "primary@example.com", "primary": True, "verified": False}]

        email, verified = provider._pick_email({}, emails)

        assert email == "primary@example.com"
        assert verified is False

    def test_github_email_pick_returns_none_when_private(self) -> None:
        """邮箱全私有 → 返回 None + 未验证。"""
        provider = GitHubProvider(config=self.make_config())

        email, verified = provider._pick_email({"email": None}, [])

        assert email is None
        assert verified is False

    def test_github_email_pick_uses_user_fallback(self) -> None:
        """没有 emails 列表时用 user_data.email。"""
        provider = GitHubProvider(config=self.make_config())

        email, verified = provider._pick_email({"email": "user@example.com"}, [])

        assert email == "user@example.com"
        assert verified is False


class TestWechatOAuthError:
    """微信错误。"""

    def test_carries_code_and_message(self) -> None:
        """错误带 errcode 与 errmsg。"""
        error = WechatOAuthError(40029, "invalid code")

        assert error.errcode == 40029
        assert "40029" in str(error)
        assert "invalid code" in str(error)
