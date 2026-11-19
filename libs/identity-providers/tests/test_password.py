"""密码 Provider 测试。"""

from __future__ import annotations

import asyncio

import pytest

from identity_providers import (
    Argon2Hasher,
    BcryptHasher,
    EmailPasswordProvider,
    InvalidCredentialError,
    generate_verification_code,
)


class TestPasswordStrength:
    """密码强度规则。"""

    def setup_method(self) -> None:
        """每个测试用同一个 provider。"""
        self.provider = EmailPasswordProvider(hasher=BcryptHasher(rounds=4))

    def test_accepts_strong_password(self) -> None:
        """强密码通过。"""
        assert self.provider.hash_password("Str0ngPassword!") is not None

    def test_rejects_short_password(self) -> None:
        """太短被拒。"""
        with pytest.raises(ValueError, match="10"):
            self.provider.hash_password("Ab1")

    def test_rejects_no_digit(self) -> None:
        """无数字被拒。"""
        with pytest.raises(ValueError, match="数字"):
            self.provider.hash_password("OnlyLettersHere")

    def test_rejects_no_letter(self) -> None:
        """无字母被拒。"""
        with pytest.raises(ValueError, match="字母"):
            self.provider.hash_password("1234567890123")

    def test_error_message_is_actionable(self) -> None:
        """⚠️ 报错要说清怎么改 —— 只说「太弱」用户不知道怎么改。"""
        with pytest.raises(ValueError) as info:
            self.provider.hash_password("short")

        message = str(info.value)
        assert "10" in message


class TestBcryptHasher:
    """bcrypt 哈希器。"""

    def test_hash_and_verify(self) -> None:
        """哈希 → 校验通过。"""
        hasher = BcryptHasher(rounds=4)
        password_hash = hasher.hash("Str0ngPassword!")

        assert hasher.verify("Str0ngPassword!", password_hash) is True

    def test_wrong_password_fails(self) -> None:
        """密码错校验失败。"""
        hasher = BcryptHasher(rounds=4)
        password_hash = hasher.hash("Str0ngPassword!")

        assert hasher.verify("WrongPassword1", password_hash) is False

    def test_same_password_gives_different_hash(self) -> None:
        """⚠️ 两次哈希不同 —— bcrypt 自带随机盐。"""
        hasher = BcryptHasher(rounds=4)

        hash_a = hasher.hash("Str0ngPassword!")
        hash_b = hasher.hash("Str0ngPassword!")

        assert hash_a != hash_b

    def test_hash_does_not_contain_plaintext(self) -> None:
        """哈希里没有明文。"""
        hasher = BcryptHasher(rounds=4)
        password_hash = hasher.hash("Str0ngPassword!")

        assert "Str0ngPassword!" not in password_hash

    def test_malformed_hash_returns_false(self) -> None:
        """哈希串坏了 → False，不抛异常。"""
        hasher = BcryptHasher(rounds=4)

        assert hasher.verify("anything", "not-a-valid-bcrypt-hash") is False


class TestArgon2Hasher:
    """argon2 哈希器。"""

    def test_hash_and_verify(self) -> None:
        """哈希 → 校验通过。"""
        pytest.importorskip("argon2")

        hasher = Argon2Hasher(time_cost=1, memory_cost=8192, parallelism=1)
        password_hash = hasher.hash("Str0ngPassword!")

        assert hasher.verify("Str0ngPassword!", password_hash) is True

    def test_wrong_password_fails(self) -> None:
        """密码错校验失败。"""
        pytest.importorskip("argon2")

        hasher = Argon2Hasher(time_cost=1, memory_cost=8192, parallelism=1)
        password_hash = hasher.hash("Str0ngPassword!")

        assert hasher.verify("WrongPassword1", password_hash) is False


class TestEmailPasswordProvider:
    """邮箱密码 Provider。"""

    def test_verify_correct_password(self) -> None:
        """正确密码通过。"""
        provider = EmailPasswordProvider(hasher=BcryptHasher(rounds=4))
        password_hash = provider.hash_password("Str0ngPassword!")

        assert provider.verify_password("Str0ngPassword!", password_hash) is True

    def test_verify_wrong_password(self) -> None:
        """错误密码失败。"""
        provider = EmailPasswordProvider(hasher=BcryptHasher(rounds=4))
        password_hash = provider.hash_password("Str0ngPassword!")

        assert provider.verify_password("WrongPassword1", password_hash) is False

    def test_async_verify_raises_on_mismatch(self) -> None:
        """异步校验失败抛 InvalidCredentialError。"""
        provider = EmailPasswordProvider(hasher=BcryptHasher(rounds=4))
        password_hash = provider.hash_password("Str0ngPassword!")

        async def run() -> None:
            await provider.verify("WrongPassword1", password_hash=password_hash)

        with pytest.raises(InvalidCredentialError):
            asyncio.run(run())

    def test_async_verify_missing_hash_raises(self) -> None:
        """缺 password_hash 抛错。"""
        provider = EmailPasswordProvider(hasher=BcryptHasher(rounds=4))

        async def run() -> None:
            await provider.verify("Str0ngPassword!")

        with pytest.raises(InvalidCredentialError):
            asyncio.run(run())


class TestVerificationCode:
    """验证码生成。"""

    def test_default_length(self) -> None:
        """默认 6 位。"""
        assert len(generate_verification_code()) == 6

    def test_custom_length(self) -> None:
        """可指定长度。"""
        assert len(generate_verification_code(length=8)) == 8

    def test_all_digits(self) -> None:
        """全是数字。"""
        assert generate_verification_code().isdigit()

    def test_codes_are_unique(self) -> None:
        """⚠️ 多次生成不重复（用 secrets 不是 random）。"""
        codes = {generate_verification_code() for _ in range(50)}

        assert len(codes) == 50
