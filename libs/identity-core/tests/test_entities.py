"""身份领域模型测试。"""

from __future__ import annotations

from uuid import uuid4

import pytest

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


class TestEmailAddress:
    """邮箱值对象。"""

    def test_normalizes_to_lowercase(self) -> None:
        """邮箱统一小写。"""
        assert EmailAddress("User@Example.COM").value == "user@example.com"

    def test_strips_whitespace(self) -> None:
        """去掉首尾空白。"""
        assert EmailAddress("  a@b.com  ").value == "a@b.com"

    def test_rejects_invalid_format(self) -> None:
        """格式非法时报错。"""
        for invalid in ["not-an-email", "a@", "@b.com", "a b@c.com", ""]:
            with pytest.raises(InvalidEmailError):
                EmailAddress(invalid)

    def test_accepts_plus_tagging(self) -> None:
        """+ 标签是合法的（过严正则会误杀）。"""
        assert EmailAddress("user+tag@example.com").value == "user+tag@example.com"

    def test_mark_verified(self) -> None:
        """标记验证。"""
        email = EmailAddress("a@b.com")
        assert email.verified is False
        assert email.mark_verified().verified is True


class TestPhoneNumber:
    """手机号值对象。"""

    def test_normalizes(self) -> None:
        """去掉空格与横线。"""
        assert PhoneNumber("138 0013-8000").value == "13800138000"

    def test_rejects_invalid_format(self) -> None:
        """格式非法时报错。"""
        for invalid in ["12345678901", "1380013800", "abcdefghijk", ""]:
            with pytest.raises(InvalidPhoneError):
                PhoneNumber(invalid)

    def test_accepts_valid_mobile(self) -> None:
        """合法手机号。"""
        assert PhoneNumber("13800138000").value == "13800138000"

    def test_mark_verified(self) -> None:
        """标记验证。"""
        assert PhoneNumber("13800138000").mark_verified().verified is True


class TestIdentity:
    """身份。"""

    def test_requires_provider_user_id(self) -> None:
        """provider_user_id 不能为空。"""
        with pytest.raises(ValueError, match="provider_user_id"):
            Identity(provider=ProviderType.WECHAT, provider_user_id="  ")

    def test_bind_to_user(self) -> None:
        """绑定到用户。"""
        user_id = uuid4()
        identity = Identity(provider=ProviderType.WECHAT, provider_user_id="oABC123")
        bound = identity.bind_to(user_id)

        assert bound.user_id == user_id
        assert bound.provider_user_id == "oABC123"

    def test_keeps_raw_provider_data(self) -> None:
        """保留第三方原始数据。"""
        identity = Identity(
            provider=ProviderType.GOOGLE,
            provider_user_id="g1",
            raw={"family_name": "张"},
        )
        assert identity.raw["family_name"] == "张"


class TestCredential:
    """凭证。"""

    def test_stores_hash_not_plaintext(self) -> None:
        """只存哈希。"""
        credential = Credential(
            user_id=uuid4(),
            credential_type=CredentialType.PASSWORD,
            secret_hash="$argon2id$v=19$...",  # noqa: S106
        )
        assert credential.secret_hash == "$argon2id$v=19$..."  # noqa: S105

    def test_touch_updates_last_used(self) -> None:
        """touch 更新最后使用时间。"""
        credential = Credential(
            user_id=uuid4(),
            credential_type=CredentialType.PASSWORD,
            secret_hash="dummy-hash",  # noqa: S106
        )
        assert credential.last_used_at is None
        assert credential.touch().last_used_at is not None


class TestUser:
    """用户。"""

    def test_create_generates_id(self) -> None:
        """创建时生成 ID。"""
        user = User.create(email=EmailAddress("a@b.com"))
        assert user.user_id is not None
        assert user.is_active is True

    def test_has_verified_email_false_by_default(self) -> None:
        """邮箱默认未验证。"""
        user = User.create(email=EmailAddress("a@b.com"))
        assert user.has_verified_email is False

    def test_has_verified_email_true_after_verification(self) -> None:
        """验证后为真。"""
        email = EmailAddress("a@b.com").mark_verified()
        user = User.create(email=email)
        assert user.has_verified_email is True

    def test_no_email_means_not_verified(self) -> None:
        """没邮箱自然没验证。"""
        assert User.create().has_verified_email is False

    def test_with_identity_binds_user_id(self) -> None:
        """绑定身份时自动填 user_id。"""
        user = User.create()
        identity = Identity(provider=ProviderType.WECHAT, provider_user_id="o1")
        updated = user.with_identity(identity)

        first = updated.identities[0]
        assert first is not None
        assert first.user_id == user.user_id
        assert updated.providers == (ProviderType.WECHAT,)

    def test_find_identity_by_provider_and_id(self) -> None:
        """按 provider + provider_user_id 查找。

        ⚠️ 微信必须用 openid 而不是昵称 —— 昵称会变。
        """
        user = User.create().with_identity(
            Identity(provider=ProviderType.WECHAT, provider_user_id="openid-123")
        )

        found = user.find_identity(ProviderType.WECHAT, "openid-123")
        assert found is not None

    def test_find_identity_returns_none_when_missing(self) -> None:
        """找不到返回 None。"""
        user = User.create().with_identity(
            Identity(provider=ProviderType.WECHAT, provider_user_id="openid-123")
        )

        assert user.find_identity(ProviderType.WECHAT, "other") is None
        assert user.find_identity(ProviderType.GOOGLE, "openid-123") is None

    def test_with_email_returns_new_instance(self) -> None:
        """不可变 —— 返回新实例。"""
        user = User.create()
        updated = user.with_email(EmailAddress("a@b.com"))

        assert user.email is None
        assert updated.email is not None
        assert updated.user_id == user.user_id

    def test_multiple_identities_same_user(self) -> None:
        """一个用户可绑多个登录方式。"""
        user = (
            User.create()
            .with_identity(Identity(provider=ProviderType.WECHAT, provider_user_id="o1"))
            .with_identity(Identity(provider=ProviderType.GOOGLE, provider_user_id="g1"))
        )

        assert len(user.identities) == 2
        assert ProviderType.WECHAT in user.providers
        assert ProviderType.GOOGLE in user.providers

    def test_does_not_mix_business_fields(self) -> None:
        """⚠️ User 不该有业务字段。

        这是旧系统 ACCOUNT 表的教训 —— 那张表把 LITELLM_PAY_KEY、
        MASTODON_PASSWORD 都塞进了身份表。
        """
        fields = set(User.__dataclass_fields__)

        for forbidden in [
            "balance",
            "quota",
            "pay_key",
            "community_password",
            "mastodon_password",
            "billing_id",
        ]:
            assert forbidden not in fields
