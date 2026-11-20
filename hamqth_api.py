"""HamQTH v2 callbook client. The CLI supplies credentials when sign-in is needed."""

import re
from collections.abc import Callable
from time import monotonic
from urllib.parse import quote

import requests


class HamQTHError(Exception):
    """Raised for any user-facing HamQTH error."""


HAM_QTH_URL = "https://www.hamqth.com/api/v2"
HTTP_TIMEOUT_SECONDS = 10
MAX_TOKEN_LIFETIME_SECONDS = 3600
PROGRAM_NAME = "ham-radio-logger"

_session: tuple[str, float] | None = None


def callbook_lookup(
    call_sign: str, *, get_credentials: Callable[[], tuple[str, str]]
) -> dict[str, str]:
    """Return the callsign and available on-air name, location, and zones."""
    global _session

    call_sign = _require_text(call_sign, "callsign")
    if (
        not re.fullmatch(r"[A-Za-z0-9]+(?:/[A-Za-z0-9]+)*", call_sign)
        or not any(character.isalpha() for character in call_sign)
        or not any(character.isdigit() for character in call_sign)
    ):
        raise HamQTHError("Enter a callsign with letters and numbers, such as AG5XY.")
    call_sign = call_sign.upper()
    path = f"/callbook/{quote(call_sign, safe='')}"

    for _ in range(2):
        token = _get_token(get_credentials)
        response = _request(
            "GET",
            path,
            headers={"Authorization": f"Bearer {token}"},
            params={"app": PROGRAM_NAME},
        )
        if response.status_code == 401:
            _session = None
            continue
        if response.status_code == 404:
            raise HamQTHError(f"{call_sign} was not found in the HamQTH callbook.")
        if response.status_code != 200:
            raise HamQTHError(
                f"HamQTH lookup failed (HTTP status {response.status_code})."
            )
        return _extract_search_fields(_json_object(response))

    raise HamQTHError(
        "HamQTH rejected the session after signing in again. Try again later."
    )


def _get_token(get_credentials: Callable[[], tuple[str, str]]) -> str:
    global _session

    if _session is not None and monotonic() < _session[1]:
        return _session[0]
    _session = None

    callsign, password = get_credentials()
    signed_in_at = monotonic()
    response = _request(
        "POST", "/login", json={"callsign": callsign, "password": password}
    )

    if response.status_code == 401:
        raise HamQTHError("HamQTH did not accept the callsign or password.")
    if response.status_code == 429:
        raise HamQTHError("HamQTH received too many sign-in attempts. Try again later.")
    if response.status_code != 200:
        raise HamQTHError(
            f"HamQTH sign-in failed (HTTP status {response.status_code})."
        )

    payload = _json_object(response)
    token = payload.get("token")
    expires_in = payload.get("expiresIn")
    if (
        not isinstance(token, str)
        or not token.strip()
        or type(expires_in) is not int
        or not 0 < expires_in <= MAX_TOKEN_LIFETIME_SECONDS
    ):
        raise HamQTHError("Unexpected sign-in response from HamQTH.")
    _session = (token, signed_in_at + expires_in)
    return token


def _request(method: str, path: str, **kwargs) -> requests.Response:
    try:
        return requests.request(
            method,
            f"{HAM_QTH_URL}{path}",
            timeout=HTTP_TIMEOUT_SECONDS,
            # A redirect could forward the login body or authorization header.
            allow_redirects=False,
            **kwargs,
        )
    except requests.exceptions.RequestException:
        raise HamQTHError("Network error contacting HamQTH.") from None


def _json_object(response: requests.Response) -> dict:
    try:
        payload = response.json()
    except ValueError:
        raise HamQTHError("Invalid JSON response from HamQTH.") from None
    if not isinstance(payload, dict):
        raise HamQTHError("Unexpected response from HamQTH. Expected a JSON object.")
    return payload


def _extract_search_fields(payload: dict) -> dict[str, str]:
    callsign = payload.get("callsign")
    if not isinstance(callsign, str) or not callsign.strip():
        raise HamQTHError("Unexpected lookup response from HamQTH. No callsign found.")

    region = payload.get("region")
    state = region.get("usState") if isinstance(region, dict) else None
    result = {"call_sign": callsign.strip().upper()}
    for field, value in (
        ("name", payload.get("nick")),
        ("city", payload.get("qth")),
        ("state", state),
        ("country", payload.get("country")),
    ):
        if isinstance(value, str) and value.strip():
            result[field] = value.strip()

    for field, zone in (
        ("cq_zone", payload.get("cq")),
        ("itu_zone", payload.get("itu")),
    ):
        if type(zone) is int:
            result[field] = str(zone)
    return result


def _require_text(value: str | None, label: str) -> str:
    text = value.strip() if value is not None else ""
    if not text:
        raise HamQTHError(f"Nothing found for {label}.")
    return text
