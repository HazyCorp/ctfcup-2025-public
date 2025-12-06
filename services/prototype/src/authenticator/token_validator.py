import json, hmac, hashlib, base64, os
from secrets import token_urlsafe

SALT = os.getenv("TOKEN_SALT")

if not SALT:
    try:
        with open("salt") as s:
            SALT = s.read()
    except FileNotFoundError:
        with open("salt", "w") as s:
            SALT = token_urlsafe(64)
            s.write(SALT)


def saltify(data: str) -> str:
    sig = hmac.new(SALT.encode(), data.encode(), hashlib.sha256).hexdigest()
    payload = json.dumps([data, sig], separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(payload).decode().rstrip("=")

def _b64url_decode(s: str) -> bytes:
    s = s.strip()
    pad = (-len(s)) % 4
    return base64.urlsafe_b64decode(s + ("=" * pad))

def unsaltify(token: str) -> str:
    try:
        raw = _b64url_decode(token)
    except Exception as e:
        raise ValueError("bad base64url") from e

    try:
        obj = json.loads(raw)
    except Exception as e:
        raise ValueError("bad json") from e

    if not (isinstance(obj, list) and len(obj) == 2):
        raise ValueError("expected [data, sig]")

    data, sig = obj
    if not isinstance(data, str) or not isinstance(sig, str):
        raise ValueError("expected data & sig as str")

    expected_sig = hmac.new(SALT.encode(), data.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(sig, expected_sig):
        raise ValueError("bad signature")

    return data
