"""state 编解码 —— 所有 OAuth2 Provider 共用的防 CSRF 机制。

⚠️ 为什么要抽成共享模块：

   微信、Google、GitHub 三家都需要 state 防护。
   如果各自实现一份，**迟早会有一家漏掉某个检查** ——
   微信那份就是漏掉「会话一致性」才出的 CSRF 漏洞。

   统一实现 = 统一行为 + 统一测试 + 改一处三处生效。

---

## state 是什么

state 是 OAuth2 的「防 CSRF 随机串」，作用是让回调方确认：
**「这个授权是我发起的，不是别人塞给我的」**。

## 本实现的三重校验

```
① 签名匹配    —— 客户端伪造不出（服务端用 state_secret 签名）
② 未过期      —— 防止重放旧的 state
③ 会话一致    —— 防止跨会话重放（单会话模式比对）
```

## 格式

```
<随机串>.<过期时间戳>.<HMAC-SHA256 签名>
```

⚠️ **state 必须由服务端生成并签名** —— 客户端生成的服务端无法校验，
客户端一旦被攻破，攻击者就能构造合法 state。
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from typing import Final

__all__ = ["STATE_PART_COUNT", "OAuth2StateCodec"]

#: state 的段数 —— <nonce>.<expires_at>.<signature>
STATE_PART_COUNT: Final = 3


class OAuth2StateCodec:
    """state 编解码器。

    ⚠️ 线程安全 —— 无状态，只读配置。
    """

    def __init__(self, secret: str, ttl: int = 300) -> None:
        """初始化。

        Args:
            secret: HMAC 签名密钥 —— **不能为空**
            ttl: 有效期（秒）

        Raises:
            ValueError: 密钥为空
        """
        if not secret:
            raise ValueError("state_secret 不能为空")

        self._secret = secret.encode("utf8")
        self._ttl = ttl

    def generate(self) -> str:
        """生成签名 state。

        Returns:
            `<nonce>.<expires_at>.<signature>`
        """
        nonce = secrets.token_urlsafe(24)
        expires_at = int(time.time()) + self._ttl
        payload = f"{nonce}.{expires_at}"
        return f"{payload}.{self._sign(payload)}"

    def verify(self, state: str, expected_state: str | None = None) -> bool:
        """校验 state。

        Args:
            state: 回调带回的 state
            expected_state: 会话中存的状态（单会话模式比对）

        Returns:
            是否有效
        """
        parsed = self._parse(state)
        if parsed is None:
            return False

        nonce, expires_at_raw, signature = parsed

        # ① 签名必须匹配 —— 客户端伪造不出来
        if not hmac.compare_digest(self._sign(f"{nonce}.{expires_at_raw}"), signature):
            return False

        # ② 必须在有效期内 —— 防重放
        if self._is_expired(expires_at_raw):
            return False

        # ③ 必须与会话一致 —— 防跨会话重放
        #    ⚠️ 用 compare_digest 而不是 == —— 防时序攻击
        session_mismatch = expected_state is not None and not hmac.compare_digest(
            expected_state, state
        )
        return not session_mismatch

    def _parse(self, state: str) -> tuple[str, str, str] | None:
        """拆解 state —— 格式不对返回 None。"""
        if not state:
            return None

        parts = state.split(".")
        if len(parts) != STATE_PART_COUNT:
            return None

        nonce, expires_at_raw, signature = parts
        if not nonce or not expires_at_raw or not signature:
            return None

        return nonce, expires_at_raw, signature

    def _is_expired(self, expires_at_raw: str) -> bool:
        """是否已过期 —— 时间戳不合法也算过期。"""
        try:
            expires_at = int(expires_at_raw)
        except ValueError:
            return True

        return time.time() > expires_at

    def _sign(self, payload: str) -> str:
        """HMAC-SHA256 签名。"""
        return hmac.new(self._secret, payload.encode("utf8"), hashlib.sha256).hexdigest()
