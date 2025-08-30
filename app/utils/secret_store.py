#!/usr/bin/env python3
"""
MVP-хранилище секретов с симметричным шифрованием без внешних зависимостей.
- Шифрование: потоковый шифр на базе HMAC-SHA256 (keystream) + HMAC-тег целостности.
- Ключ: из переменной окружения SECRET_ENC_KEY (строка), приводим к 32 байтам через SHA256.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Tuple


def _get_master_key() -> bytes:
    secret = os.getenv("SECRET_ENC_KEY", "feature-factory-mvp-default-key")
    return hashlib.sha256(secret.encode("utf-8")).digest()


def _hkdf_expand(key: bytes, info: bytes, length: int) -> bytes:
    out = b""
    counter = 1
    last = b""
    while len(out) < length:
        last = hmac.new(key, last + info + bytes([counter]), hashlib.sha256).digest()
        out += last
        counter += 1
    return out[:length]


def _keystream(key: bytes, nonce: bytes, length: int) -> bytes:
    # Генерируем псевдокейсрим через HKDF(HMAC-SHA256)
    return _hkdf_expand(key, b"stream:" + nonce, length)


def _hmac_tag(key: bytes, nonce: bytes, ciphertext: bytes) -> bytes:
    return hmac.new(key, b"tag:" + nonce + ciphertext, hashlib.sha256).digest()


def encrypt_value(plaintext: str) -> str:
    data = plaintext.encode("utf-8")
    key = _get_master_key()
    # 12-байтовый nonce
    nonce = os.urandom(12)
    stream = _keystream(key, nonce, len(data))
    ct = bytes([a ^ b for a, b in zip(data, stream)])
    tag = _hmac_tag(key, nonce, ct)
    blob = nonce + tag + ct
    return base64.b64encode(blob).decode("ascii")


def decrypt_value(blob_b64: str) -> str:
    raw = base64.b64decode(blob_b64)
    nonce = raw[:12]
    tag = raw[12:44]
    ct = raw[44:]
    key = _get_master_key()
    exp = _hmac_tag(key, nonce, ct)
    if not hmac.compare_digest(exp, tag):
        raise ValueError("Secret integrity check failed")
    stream = _keystream(key, nonce, len(ct))
    pt = bytes([a ^ b for a, b in zip(ct, stream)])
    return pt.decode("utf-8")


def mask_value(val: str) -> str:
    if not val:
        return ""
    # Оставляем последние 4 символа, остальное маскируем
    last4 = val[-4:]
    return "****" + last4

