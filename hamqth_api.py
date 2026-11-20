"""
hamqth_api.py

Purpose:
- Provide a small, testable interface for HamQTH callbook lookups.
- Hide all HamQTH details (session login, XML parsing, URLs) from the CLI.

Rules:
- Do NOT use input() or print() in this module.
- Do NOT read/write your JSONL log here.
- Raise HamQTHError with human-friendly messages when something goes wrong.
- Session handling stays inside this module.

Public interface (what your main program will import/use):
- HamQTHError
- callbook_lookup(call_sign: str) -> dict
"""

import os
import re
import xml.etree.ElementTree as ET
from time import monotonic

import requests


class HamQTHError(Exception):
    """Raised for any user-facing HamQTH error."""


ENV_HAMQTH_USER = "HAMQTH_USER"
ENV_HAMQTH_PASS = "HAMQTH_PASS"
HAM_QTH_URL = "https://www.hamqth.com/xml.php"
HAM_QTH_NS = "{https://www.hamqth.com}"
HTTP_TIMEOUT_SECONDS = 10
SESSION_LIFETIME_SECONDS = 3600
PROGRAM_NAME = "ham-radio-logger"

_session: tuple[str, float] | None = None


# -----------------------------
# Public API
# -----------------------------
def callbook_lookup(call_sign: str) -> dict:
    """
    Look up a callsign in the HamQTH callbook.

    Input:
    - call_sign: user-provided callsign string (may have whitespace/lowercase)

    Output (V1 fields):
    - dict containing:
        - call_sign (always present on success)
        - name (optional)
        - city (optional)
        - state (optional)
        - country (optional)
        - cq_zone (optional)
        - itu_zone (optional)

    Errors:
    - Raise HamQTHError if:
        - credentials are missing
        - network/HTTP fails
        - login fails
        - callsign not found
        - response format is unexpected
    """
    global _session

    call_sign = _require_text(call_sign, "callsign")
    if (
        not re.fullmatch(r"[A-Za-z0-9]+(?:/[A-Za-z0-9]+)*", call_sign)
        or not any(character.isalpha() for character in call_sign)
        or not any(character.isdigit() for character in call_sign)
    ):
        raise HamQTHError("Enter a callsign with letters and numbers, such as AG5XY.")
    call_sign = call_sign.upper()

    for _ in range(2):
        params = {"id": _get_session_id(), "callsign": call_sign, "prg": PROGRAM_NAME}
        root = _parse_xml(_http_get(HAM_QTH_URL, params))
        error = _extract_error_message(root)
        if _is_session_error(error):
            _session = None
            continue
        if _is_not_found_error(error):
            raise HamQTHError(f"{call_sign} was not found in the HamQTH callbook.")
        if error:
            raise HamQTHError(f"HamQTH lookup failed: {error}")
        return _extract_search_fields(root)

    raise HamQTHError(
        "HamQTH rejected the session after signing in again. Try again later."
    )


# -----------------------------
# Internal helpers (private)
# -----------------------------
def _load_credentials() -> tuple[str, str]:
    """
    - Read HAMQTH_USER and HAMQTH_PASS from environment variables.
    - If they exists return them
    - If one does not, raise an exception
    """

    user_name = os.getenv(ENV_HAMQTH_USER)
    if user_name is None:
        user_name = ""
    user_name = user_name.strip()

    user_pw = os.getenv(ENV_HAMQTH_PASS)
    if user_pw is None:
        user_pw = ""
    user_pw = user_pw.strip()

    if not user_name or not user_pw:

        # We do not have a value for one of these, so rais an exception

        raise HamQTHError(
            "HamQTH credentials not set. Please set HAMQTH_USER and HAMQTH_PASS."
        )

    return user_name, user_pw


def _get_session_id() -> str:
    """Reuse the current session until its one-hour lifetime ends."""
    global _session

    now = monotonic()
    if _session is not None:
        session_id, expires_at = _session
        if now < expires_at:
            return session_id

    session_id = _login_and_create_session()
    _session = (session_id, now + SESSION_LIFETIME_SECONDS)
    return session_id


def _login_and_create_session() -> str:
    """Log in to HamQTH and return the session ID from the response."""
    user_name, user_pw = _load_credentials()
    request_params = {"u": user_name, "p": user_pw}
    xml_text = _http_get(HAM_QTH_URL, request_params)
    xml_root = _parse_xml(xml_text)
    error = _extract_error_message(xml_root)
    if error:
        raise HamQTHError(f"HamQTH login failed: {error}")
    session_id = _extract_session_id(xml_root)
    if session_id is None:
        raise HamQTHError("HamQTH login did not return a session ID.")
    return session_id


def _http_get(url: str, params: dict) -> str:
    try:
        response = requests.get(url, params=params, timeout=HTTP_TIMEOUT_SECONDS)
    except requests.exceptions.RequestException as exc:
        raise HamQTHError("Network error contacting HamQTH.") from exc

    if response.status_code != 200:
        raise HamQTHError(f"HTTP error from HamQTH (status {response.status_code}).")

    return response.text


def _parse_xml(xml_text: str):
    try:
        return ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise HamQTHError("Invalid XML response from HamQTH.") from exc


def _extract_error_message(root) -> str | None:
    search_error_message = _find_first_element(root, "error")
    if search_error_message != None:
        error_message = search_error_message.text
        if error_message:
            error_message = error_message.strip()
            return error_message
        else:
            return None
    else:
        return None


def _extract_session_id(root) -> str | None:
    search_session_id = _find_first_element(root, "session_id")

    if search_session_id is None:
        return None
    session_id = search_session_id.text
    if session_id:
        session_id = session_id.strip()
        if session_id == "":
            return None
        else:
            return session_id
    else:
        return None


def _extract_search_fields(root) -> dict:
    """Map HamQTH's XML fields to the fields used by the logger."""
    search = _find_first_element(root, "search")
    if search is None:
        raise HamQTHError(
            "Unexpected lookup response from HamQTH. No search result found."
        )

    fields = {
        child.tag.removeprefix(HAM_QTH_NS).lower(): (child.text or "").strip()
        for child in search
    }
    call_sign = fields.get("callsign")
    if not call_sign:
        raise HamQTHError("Unexpected lookup response from HamQTH. No callsign found.")

    result = {"call_sign": call_sign.upper()}
    for xml_field, result_field in (
        ("nick", "name"),
        ("qth", "city"),
        ("us_state", "state"),
        ("country", "country"),
        ("cq", "cq_zone"),
        ("itu", "itu_zone"),
    ):
        value = fields.get(xml_field)
        if value:
            result[result_field] = value
    return result


def _is_session_error(err_msg: str | None) -> bool:
    if err_msg is None:
        return False
    err_msg = err_msg.strip().lower()
    return "session does not exist or expired" in err_msg


def _is_not_found_error(err_msg: str | None) -> bool:
    if err_msg is None:
        return False
    err_msg = err_msg.strip().lower()
    return "callsign not found" in err_msg


def _require_text(value: str, label: str) -> str:
    if value is None:
        raise HamQTHError(f"Nothing found for {label}.")

    text = value.strip()
    if not text:
        raise HamQTHError(f"Nothing found for {label}.")

    return text


def _find_first_element(root, tag_name):

    # We want to find the element with or without the name space stuff for HamQTH
    # so first let's look for it with name space, and if we find it return it, or None if not

    search_element_namespace = root.find(".//" + HAM_QTH_NS + tag_name)
    if search_element_namespace is None:

        # OK, not found with name space. See if we can find with no name space

        search_element_no_namespace = root.find(".//" + tag_name)
        if search_element_no_namespace is None:
            return None
        return search_element_no_namespace
    else:
        return search_element_namespace
