"""邮箱 + 密码登录。

⚠️ 密码处理原则：

1. **永不存明文** —— 只存哈希
2. **不用 MD5/SHA1** —— 必须用 argon2 或 bcrypt（自带盐 + 可调成本）
3. **哈希算法可替换** —— 端口化，将来换 argon2 → bcrypt 不影响调用方
4. **验证失败不区分「用户不存在」与「密码错误」** —— 防用户名枚举

⚠️ 本模块只做**校验**（verify）—— 不负责注册时设置密码。
   注册的密码哈希由 application 层调用 hasher.hash() 完成。
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from typing import Final, Protocol, runtime_checkable

from identity_core.entities import ProviderType

from identity_providers.base import InvalidCredentialError, ProviderProfile

#: 密码最小长度
MIN_PASSWORD_LENGTH: Final = 10

__all__ = ["Argon2Hasher", "BcryptHasher", "EmailPasswordProvider", "PasswordHasher"]


@runtime_checkable
class PasswordHasher(Protocol):
    """密码哈希器端口。

    ⚠️ 端口化是为了将来能替换算法而不动调用方。
    """

    def hash(self, password: str) -> str:
        """哈希密码。

        Args:
            password: 明文密码

        Returns:
            哈希串（含算法参数与盐）
        """
        ...

    def verify(self, password: str, password_hash: str) -> bool:
        """校验密码。

        Args:
            password: 明文密码
            password_hash: 存储的哈希

        Returns:
            是否匹配
        """
        ...


@dataclass(frozen=True, slots=True)
class Argon2Hasher:
    """argon2id 哈希器 —— 推荐默认。

    ⚠️ 需要 `argon2-cffi` 包。没装的话本类不可用，
       但接口不变 —— 换成 BcryptHasher 即可。
    """

    #: 时间成本 —— 越大越慢越安全
    time_cost: int = 3
    #: 内存成本（KiB）—— argon2 的主要抗 GPU 手段
    memory_cost: int = 65536
    #: 并行度
    parallelism: int = 4

    def hash(self, password: str) -> str:
        """哈希密码。"""
        # ⚠️ 延迟 import —— argon2-cffi 是**可选依赖**（见 pyproject 的
        #    [project.optional-dependencies].hashing）。顶层 import 会让
        #    没装 argon2 的环境连 import 本模块都失败。
        from argon2 import PasswordHasher as _Argon2  # noqa: PLC0415

        hasher = _Argon2(
            time_cost=self.time_cost,
            memory_cost=self.memory_cost,
            parallelism=self.parallelism,
        )
        return hasher.hash(password)

    def verify(self, password: str, password_hash: str) -> bool:
        """校验密码。

        ⚠️ 校验失败**不抛异常** —— 返回 False 即可。
           区分「密码错」和「哈希格式坏」对攻击者没有价值。
        """
        from argon2 import PasswordHasher as _Argon2  # noqa: PLC0415
        from argon2.exceptions import VerifyMismatchError  # noqa: PLC0415

        hasher = _Argon2(
            time_cost=self.time_cost,
            memory_cost=self.memory_cost,
            parallelism=self.parallelism,
        )
        try:
            return hasher.verify(password_hash, password)
        except VerifyMismatchError:
            # 密码不匹配 —— 正常情况
            return False
        except Exception:  # noqa: BLE001
            # 哈希串损坏 / 参数不兼容 —— 也当不匹配
            # ⚠️ 对攻击者而言，区分这两种失败没有价值
            return False


@dataclass(frozen=True, slots=True)
class BcryptHasher:
    """bcrypt 哈希器 —— argon2 不可用时的备选。

    ⚠️ bcrypt 自带盐，但**只处理前 72 字节** ——
       超长密码会被静默截断（这是个历史包袱）。
    """

    #: 成本因子 —— 12 约等于 0.3 秒/次
    rounds: int = 12

    def hash(self, password: str) -> str:
        """哈希密码。"""
        import bcrypt  # noqa: PLC0415

        return bcrypt.hashpw(password.encode("utf8"), bcrypt.gensalt(self.rounds)).decode("utf8")

    def verify(self, password: str, password_hash: str) -> bool:
        """校验密码。

        ⚠️ 失败一律返回 False —— 不区分「密码错」与「哈希串坏」，
           对攻击者没有价值。
        """
        import bcrypt  # noqa: PLC0415

        try:
            return bcrypt.checkpw(password.encode("utf8"), password_hash.encode("utf8"))
        except ValueError:
            # 哈希串格式不对
            return False
        except Exception:  # noqa: BLE001
            # 其它异常（编码错误等）也当不匹配
            return False


@dataclass(frozen=True, slots=True)
class EmailPasswordProvider:
    """邮箱 + 密码 Provider。

    ⚠️ 这个 Provider **不查数据库** —— 它只做密码校验。
       「用户存在吗」「密码对不对」需要一起判断时，
       由 application 层编排（先查用户，再校验密码）。
    """

    hasher: PasswordHasher
    provider_type: ProviderType = ProviderType.EMAIL_PASSWORD

    def hash_password(self, password: str) -> str:
        """哈希密码（注册时用）。"""
        self._validate_strength(password)
        return self.hasher.hash(password)

    def verify_password(self, password: str, password_hash: str) -> bool:
        """校验密码。"""
        return self.hasher.verify(password, password_hash)

    async def verify(self, credential: str, **kwargs: object) -> ProviderProfile:
        """验证密码。

        ⚠️ 仅在已知 password_hash 时有意义。

        Args:
            credential: 明文密码
            kwargs: 需含 `password_hash` 与可选 `email`

        Raises:
            InvalidCredentialError: 密码不匹配
        """
        password_hash = kwargs.get("password_hash")
        if not isinstance(password_hash, str) or not password_hash:
            raise InvalidCredentialError("缺少 password_hash")

        if not self.hasher.verify(credential, password_hash):
            raise InvalidCredentialError("密码错误")

        email = kwargs.get("email")
        return ProviderProfile(
            provider=ProviderType.EMAIL_PASSWORD,
            provider_user_id=str(email) if email else "",
            email=str(email) if email else None,
            email_verified=bool(kwargs.get("email_verified", False)),
        )

    def _validate_strength(self, password: str) -> None:
        """校验密码强度。

        ⚠️ 强度规则要**可解释** —— 只说「太弱」用户不知道怎么改。
        """
        if len(password) < MIN_PASSWORD_LENGTH:
            raise ValueError(f"密码至少 {MIN_PASSWORD_LENGTH} 位")

        if not any(char.isdigit() for char in password):
            raise ValueError("密码需包含数字")

        if not any(char.isalpha() for char in password):
            raise ValueError("密码需包含字母")


def generate_verification_code(length: int = 6) -> str:
    """生成邮箱/短信验证码。

    ⚠️ 用 `secrets` 而非 `random` —— 验证码是可预测就会出事的东西。

    Args:
        length: 位数

    Returns:
        数字验证码字符串
    """
    return "".join(secrets.choice("0123456789") for _ in range(length))
