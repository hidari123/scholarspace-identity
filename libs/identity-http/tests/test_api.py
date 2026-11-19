"""HTTP 接口测试。"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest
from fastapi.testclient import TestClient

from identity_http import (
    InMemoryCredentialRepository,
    InMemoryUserRepository,
    InMemoryVerificationCodeRepository,
    create_app,
)
from identity_http.routers import auth


@pytest.fixture
def repos() -> dict[str, Any]:
    """每个测试一套独立的内存仓储。"""
    return {
        "users": InMemoryUserRepository(),
        "credentials": InMemoryCredentialRepository(),
        "codes": InMemoryVerificationCodeRepository(),
    }


@pytest.fixture
def client(repos: dict[str, Any]) -> TestClient:
    """带依赖覆盖的测试客户端。"""
    app = create_app()

    app.dependency_overrides[auth.get_user_repository] = lambda: repos["users"]
    app.dependency_overrides[auth.get_credential_repository] = lambda: repos["credentials"]
    app.dependency_overrides[auth.get_verification_repository] = lambda: repos["codes"]

    return TestClient(app)


class TestHealth:
    """健康检查。"""

    def test_health_ok(self, client: TestClient) -> None:
        """返回 ok。"""
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestSignup:
    """注册。"""

    def test_signup_with_email(self, client: TestClient) -> None:
        """邮箱注册成功。"""
        response = client.post(
            "/api/identity/signup",
            json={
                "method": "email",
                "email": "user@example.com",
                "password": "Str0ngPassword!",
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "completed"
        assert body["user"] is not None
        assert body["user"]["email"] == "user@example.com"

    def test_signup_persists_user(self, client: TestClient, repos: dict[str, Any]) -> None:
        """注册的用户落库了。"""
        client.post(
            "/api/identity/signup",
            json={
                "method": "email",
                "email": "user@example.com",
                "password": "Str0ngPassword!",
            },
        )

        found = repos["users"].get_by_email("user@example.com")
        assert found is not None

    def test_duplicate_email_conflicts(self, client: TestClient) -> None:
        """⚠️ 邮箱重复返回 409。"""
        payload = {
            "method": "email",
            "email": "user@example.com",
            "password": "Str0ngPassword!",
        }
        client.post("/api/identity/signup", json=payload)

        response = client.post("/api/identity/signup", json=payload)

        assert response.status_code == 409
        assert "email_taken" in str(response.json())

    def test_unknown_method_fails(self, client: TestClient) -> None:
        """未知注册方式返回 400。"""
        response = client.post(
            "/api/identity/signup",
            json={"method": "nonexistent", "email": "a@b.com"},
        )

        assert response.status_code == 400

    def test_invalid_email_rejected_by_schema(self, client: TestClient) -> None:
        """⚠️ 邮箱格式在入口就被 Pydantic 拦掉。"""
        response = client.post(
            "/api/identity/signup",
            json={"method": "email", "email": "not-an-email", "password": "Str0ngPassword!"},
        )

        assert response.status_code == 422

    def test_short_password_rejected_by_schema(self, client: TestClient) -> None:
        """⚠️ 太短的密码在入口被拦（不用等到哈希层）。"""
        response = client.post(
            "/api/identity/signup",
            json={"method": "email", "email": "a@b.com", "password": "short"},
        )

        assert response.status_code == 422

    def test_response_has_no_secret_fields(self, client: TestClient) -> None:
        """⚠️ 响应里不能有密码哈希或 token。"""
        response = client.post(
            "/api/identity/signup",
            json={
                "method": "email",
                "email": "user@example.com",
                "password": "Str0ngPassword!",
            },
        )

        body = response.json()
        assert "password" not in body["user"]
        assert "password_hash" not in body["user"]
        assert "secret_hash" not in body["user"]
        assert "access_token" not in body["user"]


class TestLogin:
    """登录。"""

    def test_login_success(self, client: TestClient) -> None:
        """登录成功。"""
        # 先注册（注册会存密码凭证）
        client.post(
            "/api/identity/signup",
            json={
                "method": "email",
                "email": "user@example.com",
                "password": "Str0ngPassword!",
            },
        )

        response = client.post(
            "/api/identity/login",
            json={"method": "email", "email": "user@example.com", "password": "Str0ngPassword!"},
        )

        assert response.status_code == 200
        assert response.json()["user"]["email"] == "user@example.com"

    def test_login_wrong_password(self, client: TestClient) -> None:
        """密码错返回 401。"""
        client.post(
            "/api/identity/signup",
            json={
                "method": "email",
                "email": "user@example.com",
                "password": "Str0ngPassword!",
            },
        )

        response = client.post(
            "/api/identity/login",
            json={"method": "email", "email": "user@example.com", "password": "WrongPassword1"},
        )

        assert response.status_code == 401

    def test_login_unknown_user_same_error(self, client: TestClient) -> None:
        """⚠️ 用户不存在与密码错误返回**同样的**错误。

        区分两者会泄露「这个邮箱注册过」。
        """
        response = client.post(
            "/api/identity/login",
            json={"method": "email", "email": "nobody@example.com", "password": "Str0ngPassword!"},
        )

        assert response.status_code == 401
        assert "invalid_credentials" in str(response.json())

    def test_login_unsupported_method(self, client: TestClient) -> None:
        """暂不支持的方式返回 400。"""
        response = client.post(
            "/api/identity/login",
            json={"method": "wechat", "email": "a@b.com"},
        )

        assert response.status_code == 400


class TestVerificationCode:
    """验证码。"""

    def test_send_code_returns_202(self, client: TestClient) -> None:
        """发送验证码返回 202。"""
        response = client.post(
            "/api/identity/verification-code",
            json={"target": "user@example.com", "purpose": "register"},
        )

        assert response.status_code == 202

    def test_response_does_not_leak_code(self, client: TestClient) -> None:
        """⚠️ 响应里不能有验证码 —— 那是绕过邮箱验证。"""
        response = client.post(
            "/api/identity/verification-code",
            json={"target": "user@example.com", "purpose": "register"},
        )

        body = response.json()
        assert "code" not in body
        assert "verification_code" not in body

    def test_verify_wrong_code_fails(self, client: TestClient) -> None:
        """错误验证码返回 400。"""
        client.post(
            "/api/identity/verification-code",
            json={"target": "user@example.com", "purpose": "register"},
        )

        response = client.post(
            "/api/identity/verification-code/verify",
            json={"target": "user@example.com", "code": "000000", "purpose": "register"},
        )

        assert response.status_code == 400

    def test_verify_correct_code_passes(self, client: TestClient, repos: dict[str, Any]) -> None:
        """正确验证码通过。"""
        await_code = repos["codes"]
        asyncio.run(await_code.store("user@example.com", "123456", "register"))

        response = client.post(
            "/api/identity/verification-code/verify",
            json={"target": "user@example.com", "code": "123456", "purpose": "register"},
        )

        assert response.status_code == 200
        assert response.json()["valid"] is True

    def test_code_is_single_use(self, client: TestClient, repos: dict[str, Any]) -> None:
        """⚠️ 验证码一次性 —— 用过就失效。"""
        asyncio.run(repos["codes"].store("user@example.com", "123456", "register"))

        first = client.post(
            "/api/identity/verification-code/verify",
            json={"target": "user@example.com", "code": "123456", "purpose": "register"},
        )
        second = client.post(
            "/api/identity/verification-code/verify",
            json={"target": "user@example.com", "code": "123456", "purpose": "register"},
        )

        assert first.status_code == 200
        assert second.status_code == 400

    def test_code_purpose_isolated(self, client: TestClient, repos: dict[str, Any]) -> None:
        """⚠️ 不同用途的码互不通用。"""
        asyncio.run(repos["codes"].store("user@example.com", "123456", "register"))

        response = client.post(
            "/api/identity/verification-code/verify",
            json={"target": "user@example.com", "code": "123456", "purpose": "reset_password"},
        )

        assert response.status_code == 400


class TestWechat:
    """微信。"""

    def test_authorize_requires_config(self, client: TestClient, monkeypatch: Any) -> None:
        """⚠️ 没配置微信密钥时返回 503 —— 不静默降级。"""
        for name in (
            "WECHAT_APPID",
            "WECHAT_SECRET",
            "WECHAT_REDIRECT_URI",
            "IDENTITY_STATE_SECRET",
        ):
            monkeypatch.delenv(name, raising=False)

        response = client.get("/api/identity/wechat/authorize")

        assert response.status_code == 503
        assert "not_configured" in str(response.json())

    def test_authorize_returns_url_and_state(self, client: TestClient, monkeypatch: Any) -> None:
        """配置齐全时返回授权 URL 与 state。"""
        monkeypatch.setenv("WECHAT_APPID", "wx-test")
        monkeypatch.setenv("WECHAT_SECRET", "secret-test")
        monkeypatch.setenv("WECHAT_REDIRECT_URI", "https://example.com/cb")
        monkeypatch.setenv("IDENTITY_STATE_SECRET", "state-secret")

        response = client.get("/api/identity/wechat/authorize")

        assert response.status_code == 200
        body = response.json()
        assert body["authorize_url"].startswith("https://open.weixin.qq.com/connect/qrconnect")
        assert body["state"] is not None

    def test_callback_rejects_bad_state(self, client: TestClient, monkeypatch: Any) -> None:
        """⚠️ 伪造 state 的回调被拒（CSRF 防护）。"""
        monkeypatch.setenv("WECHAT_APPID", "wx-test")
        monkeypatch.setenv("WECHAT_SECRET", "secret-test")
        monkeypatch.setenv("WECHAT_REDIRECT_URI", "https://example.com/cb")
        monkeypatch.setenv("IDENTITY_STATE_SECRET", "state-secret")

        response = client.post(
            "/api/identity/wechat/callback",
            json={"code": "fake-code", "state": "forged.nonce.badsig"},
        )

        assert response.status_code == 401


class TestOpenAPI:
    """API 文档。"""

    def test_openapi_generates(self, client: TestClient) -> None:
        """OpenAPI 文档能生成 —— 说明 schema 没写错。"""
        response = client.get("/openapi.json")

        assert response.status_code == 200
        paths = response.json()["paths"]
        assert "/api/identity/signup" in paths
        assert "/api/identity/login" in paths
