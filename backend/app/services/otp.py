"""Phone-number verification by one-time code.

The code is sent through the configured SMS gateway (`app/services/sms.py`). It
is echoed back in the API response **only** when the gateway does not actually
deliver anything — the default `console` provider, which logs instead of
sending. That condition is derived from the provider itself rather than from a
flag someone could leave switched on: the moment a real gateway is configured,
the code stops being readable by whoever asked for it, with no second setting to
remember. Production refuses to echo it under any provider.

Codes live in the shared cache (Redis when configured, in-process otherwise), so
they expire on their own and never touch the database.
"""
from __future__ import annotations

import hashlib
import hmac
import re
import secrets
from dataclasses import dataclass
from typing import Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.services.cache import cache
from app.services.sms import SmsError, get_sms_provider

log = get_logger("auth.otp")

MAX_ATTEMPTS = 5
_KEY = "otp:phone:"
# E.164-ish: an optional +, then 8-15 digits. Indian 10-digit numbers are
# normalised to +91 below so the same phone can't register twice.
_PHONE_RE = re.compile(r"^\+?[1-9]\d{7,14}$")


class OtpError(Exception):
    """The phone number, the code, or the attempt count is not acceptable."""


@dataclass
class OtpChallenge:
    phone: str
    expires_in_seconds: int
    debug_code: Optional[str]  # populated outside production only


def normalise_phone(raw: str) -> str:
    """`98765 43210` / `+91 98765-43210` / `09876543210` all become `+919876543210`."""
    digits = re.sub(r"[^\d+]", "", raw or "")
    if digits.startswith("00"):
        digits = "+" + digits[2:]
    if not digits.startswith("+"):
        digits = digits.lstrip("0")
        if len(digits) == 10:  # bare Indian mobile number
            digits = "+91" + digits
        else:
            digits = "+" + digits
    if not _PHONE_RE.match(digits):
        raise OtpError("That doesn't look like a valid phone number")
    return digits


def _hash(code: str, phone: str) -> str:
    """Store a keyed digest, never the code itself."""
    return hmac.new(settings.secret_key.encode(), f"{phone}:{code}".encode(), hashlib.sha256).hexdigest()


def start_challenge(raw_phone: str, payload: Optional[dict] = None) -> OtpChallenge:
    """Issue a code for `raw_phone`, optionally parking data until it's confirmed.

    Registration uses `payload` to hold the name and password hash: nothing is
    written to the database until the person proves they own the number, so an
    abandoned sign-up leaves no half-made account behind.
    """
    phone = normalise_phone(raw_phone)
    code = f"{secrets.randbelow(1_000_000):06d}"
    ttl = settings.otp_ttl_minutes * 60

    provider = get_sms_provider()
    try:
        provider.send(phone, f"{code} is your Disha AI verification code. It expires in "
                             f"{settings.otp_ttl_minutes} minutes. Do not share it with anyone.")
    except SmsError:
        # Nothing is stored, so the user can simply try again — and no dead
        # challenge is left behind to burn one of their attempts later.
        raise OtpError("Could not send the code right now. Please try again.") from None

    cache.set_json(
        _KEY + phone,
        {"hash": _hash(code, phone), "attempts": 0, "payload": payload or {}},
        ttl=ttl,
    )
    log.info("otp_issued", phone=phone, provider=provider.name)

    # Echo the code only when nothing was really sent, and never in production.
    expose = not provider.delivers_real_messages and not settings.is_production
    return OtpChallenge(phone=phone, expires_in_seconds=ttl, debug_code=code if expose else None)


def peek_payload(raw_phone: str) -> Optional[dict]:
    """The data parked with a live challenge, for re-sending a code.

    Deliberately does not expose the code hash or touch the attempt counter — a
    resend must not become a way to reset a burnt-through attempt budget.
    """
    record = cache.get_json(_KEY + normalise_phone(raw_phone))
    return (record or {}).get("payload") or None


def verify_challenge(raw_phone: str, code: str) -> tuple[str, dict]:
    """Return `(normalised phone, parked payload)`; raise [OtpError] otherwise."""
    phone = normalise_phone(raw_phone)
    record = cache.get_json(_KEY + phone)
    if not record:
        raise OtpError("That code has expired. Please request a new one.")

    if record["attempts"] >= MAX_ATTEMPTS:
        cache.delete(_KEY + phone)
        raise OtpError("Too many incorrect attempts. Please request a new code.")

    if not hmac.compare_digest(record["hash"], _hash((code or "").strip(), phone)):
        record["attempts"] += 1
        cache.set_json(_KEY + phone, record, ttl=settings.otp_ttl_minutes * 60)
        remaining = MAX_ATTEMPTS - record["attempts"]
        raise OtpError(f"Incorrect code. {remaining} attempt(s) left.")

    cache.delete(_KEY + phone)  # single use
    return phone, record.get("payload") or {}
