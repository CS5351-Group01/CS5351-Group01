"""认证服务：密码哈希 + JWT 签发/校验。

不引第三方库，纯标准库实现 HS256 JWT。
生产要换 APP_SECRET，否则所有人共用同一个默认密钥。
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time

ALGORITHM = "HS256"
_ITERATIONS = 120_000


def _secret() -> bytes:
    return os.environ.get("APP_SECRET", "dev-secret-change-me").encode()


# ---------------------------------------------------------------- 密码

def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(8)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), _ITERATIONS)
    return f"pbkdf2_sha256${salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, salt, _ = stored.split("$")
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    return hmac.compare_digest(hash_password(password, salt), stored)


# ---------------------------------------------------------------- JWT

def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64decode(text: str) -> bytes:
    padding = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + padding)


def create_access_token(subject: str, expires_in: int = 1800) -> str:
    now = int(time.time())
    header = {"alg": ALGORITHM, "typ": "JWT"}
    payload = {"sub": subject, "iat": now, "exp": now + expires_in}
    segments = [
        _b64encode(json.dumps(header, separators=(",", ":")).encode()),
        _b64encode(json.dumps(payload, separators=(",", ":")).encode()),
    ]
    signing_input = ".".join(segments).encode()
    signature = hmac.new(_secret(), signing_input, hashlib.sha256).digest()
    segments.append(_b64encode(signature))
    return ".".join(segments)


def decode_token(token: str) -> dict:
    """校验签名和过期时间；任何异常都抛 ValueError，由调用方转成 401。"""
    try:
        head, body, signature = token.split(".")
    except ValueError as exc:
        raise ValueError("token 格式不正确") from exc

    signing_input = f"{head}.{body}".encode()
    expected = hmac.new(_secret(), signing_input, hashlib.sha256).digest()
    if not hmac.compare_digest(expected, _b64decode(signature)):
        raise ValueError("签名不匹配")

    try:
        payload = json.loads(_b64decode(body))
    except Exception as exc:
        raise ValueError("payload 无法解析") from exc

    if int(payload.get("exp", 0)) < int(time.time()):
        raise ValueError("token 已过期")
    return payload
