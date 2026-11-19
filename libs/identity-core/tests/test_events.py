"""领域事件测试。"""

from __future__ import annotations

from uuid import uuid4

from identity_core.events import (
    IdentityBound,
    UserEmailBound,
    UserLoggedIn,
    UserRegistered,
)


class TestUserRegistered:
    """注册事件。"""

    def test_payload_contains_user_and_email(self) -> None:
        """负载含用户与邮箱。"""
        user_id = uuid4()
        event = UserRegistered(
            user_id=user_id,
            email="a@b.com",
            providers=("wechat", "email_password"),
        )

        payload = event.payload()
        assert payload["user_id"] == str(user_id)
        assert payload["email"] == "a@b.com"
        assert payload["providers"] == ["wechat", "email_password"]

    def test_to_dict_is_serializable(self) -> None:
        """可序列化 —— 跨进程投递需要。"""
        event = UserRegistered(user_id=uuid4(), email="a@b.com")
        data = event.to_dict()

        assert data["event_type"] == "identity.user_registered"
        assert isinstance(data["event_id"], str)
        assert isinstance(data["occurred_at"], str)

    def test_event_types_are_distinct(self) -> None:
        """事件类型互不相同 —— 订阅方按类型过滤。"""
        types = {
            UserRegistered().event_type,
            UserEmailBound().event_type,
            UserLoggedIn().event_type,
            IdentityBound().event_type,
        }
        assert len(types) == 4

    def test_tenant_id_carried(self) -> None:
        """租户 ID 随事件传递 —— 多租户分流用。"""
        event = UserRegistered(user_id=uuid4(), tenant_id="acme")
        assert event.to_dict()["tenant_id"] == "acme"


class TestIdentityBound:
    """身份绑定事件。"""

    def test_payload_has_provider(self) -> None:
        """负载含 provider 与 provider_user_id。"""
        event = IdentityBound(
            user_id=uuid4(),
            provider="google",
            provider_user_id="g123",
        )

        payload = event.payload()
        assert payload["provider"] == "google"
        assert payload["provider_user_id"] == "g123"
