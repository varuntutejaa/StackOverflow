"""SMS delivery for one-time codes.

Two providers behind one interface:

* **console** (default) — logs the message instead of sending it. Keeps a fresh
  clone working with zero credentials, which is how the rest of this codebase's
  AI providers behave too.
* **twilio** — a real send over Twilio's REST API. `httpx` only, so no extra
  dependency; the SDK would buy nothing for a single POST.

Adding another gateway (MSG91, Gupshup, an Indian DLT-registered sender) means
one more `SmsProvider` subclass and one line in `get_sms_provider`.
"""
from __future__ import annotations

import abc

import httpx

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger("sms")


class SmsError(Exception):
    """The message could not be handed to the gateway."""


class SmsProvider(abc.ABC):
    name: str = "base"

    @abc.abstractmethod
    def send(self, to: str, body: str) -> None:
        """Deliver `body` to the E.164 number `to`, or raise [SmsError]."""

    @property
    def delivers_real_messages(self) -> bool:
        """False when nothing actually leaves the building.

        This is what decides whether the OTP may be echoed back in the API
        response: if no SMS is truly sent, the code has to reach the user
        somehow, and if one *is* sent it must never be readable by the caller.
        """
        return True


class ConsoleSmsProvider(SmsProvider):
    """Logs the message. The code is echoed to the client — see the property below."""

    name = "console"

    def send(self, to: str, body: str) -> None:
        log.info("sms_console", to=to, body=body)

    @property
    def delivers_real_messages(self) -> bool:
        return False


class TwilioSmsProvider(SmsProvider):
    name = "twilio"

    def __init__(self) -> None:
        missing = [
            key
            for key, value in (
                ("TWILIO_ACCOUNT_SID", settings.twilio_account_sid),
                ("TWILIO_AUTH_TOKEN", settings.twilio_auth_token),
                ("TWILIO_FROM_NUMBER", settings.twilio_from_number),
            )
            if not value
        ]
        if missing:
            raise ValueError(f"Twilio is not fully configured: {', '.join(missing)}")

    def send(self, to: str, body: str) -> None:
        url = (
            "https://api.twilio.com/2010-04-01/Accounts/"
            f"{settings.twilio_account_sid}/Messages.json"
        )
        try:
            response = httpx.post(
                url,
                auth=(settings.twilio_account_sid, settings.twilio_auth_token),
                data={"To": to, "From": settings.twilio_from_number, "Body": body},
                timeout=15,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            # Log the number but never the body — it carries the code.
            log.warning("sms_send_failed", provider=self.name, to=to, error=str(exc))
            raise SmsError("Could not send the verification code. Please try again.") from exc


def get_sms_provider() -> SmsProvider:
    """Resolve the configured provider, falling back to console on misconfiguration.

    Not cached: a provider that failed to construct because a credential was
    missing should start working the moment the environment is fixed and the
    process restarts — and a per-OTP construction cost is irrelevant next to the
    network call it is about to make.
    """
    choice = (settings.sms_provider or "console").lower()
    if choice == "twilio":
        try:
            return TwilioSmsProvider()
        except ValueError as exc:
            log.warning("sms_provider_fallback", requested=choice, error=str(exc))
    return ConsoleSmsProvider()
