from hamqth_api import (
    _is_session_error,
    _is_not_found_error,
    _extract_session_id,
    _parse_xml,
    _find_first_element,
)
import hamqth_api
import pytest
import requests
import xml.etree.ElementTree as ET


def test_is_session_error_returns_true_for_expired_session_message():
    assert _is_session_error("Session does not exist or expired") is True


def test_is_session_error_returns_false_for_none():
    assert _is_session_error(None) is False


def test_is_not_found_error_returns_true_for_callsign_not_found():
    assert _is_not_found_error("Callsign not found") is True


def test_is_not_found_error_returns_false_for_callsign_none():
    assert _is_not_found_error(None) is False


def test_extract_session_id_returns_session_id_text():
    session_root = _parse_xml(
        "<HamQTH><session><session_id>abc123</session_id></session></HamQTH>"
    )
    session_id = _extract_session_id(session_root)
    assert "abc123" == session_id


def test_extract_session_id_returns_none_no_session_id_found():
    session_root = _parse_xml("<HamQTH><session></session></HamQTH>")
    session_id = _extract_session_id(session_root)
    assert session_id is None


def test_extract_session_id_returns_none_empyt_session_id():
    session_root = _parse_xml(
        "<HamQTH><session><session_id></session_id></session></HamQTH>"
    )
    session_id = _extract_session_id(session_root)
    assert session_id is None


def test_extract_session_id_returns_none_session_id_whitespace():
    session_root = _parse_xml(
        "<HamQTH><session><session_id>    </session_id></session></HamQTH>"
    )
    session_id = _extract_session_id(session_root)
    assert session_id is None


def test_login_and_create_session_returns_session_id(monkeypatch):
    def fake_http_get(url, params):
        return """
        <HamQTH version="2.7" xmlns="https://www.hamqth.com">
            <session>
                <session_id>ABC123</session_id>
            </session>
        </HamQTH>
        """

    monkeypatch.setattr(hamqth_api, "_http_get", fake_http_get)
    monkeypatch.setenv("HAMQTH_USER", "testuser")
    monkeypatch.setenv("HAMQTH_PASS", "testpass")

    assert hamqth_api._login_and_create_session() == "ABC123"


@pytest.mark.parametrize(
    ("session_xml", "message"),
    [
        ("<error>Wrong user name or password</error>", "Wrong user name or password"),
        ("<session_id> </session_id>", "did not return a session ID"),
    ],
)
def test_login_rejects_unsuccessful_responses(monkeypatch, session_xml, message):
    monkeypatch.setenv("HAMQTH_USER", "testuser")
    monkeypatch.setenv("HAMQTH_PASS", "testpass")
    monkeypatch.setattr(
        hamqth_api,
        "_http_get",
        lambda url, params: (
            '<HamQTH xmlns="https://www.hamqth.com">'
            f"<session>{session_xml}</session></HamQTH>"
        ),
    )

    with pytest.raises(hamqth_api.HamQTHError, match=message):
        hamqth_api._login_and_create_session()


def test_find_first_element_handles_namespace():
    xml = """
    <HamQTH version="2.7" xmlns="https://www.hamqth.com">
        <session>
            <session_id>ABC123</session_id>
        </session>
    </HamQTH>
    """
    root = ET.fromstring(xml)

    element = _find_first_element(root, "session_id")

    assert element is not None
    assert element.text == "ABC123"


def test_find_first_element_handles_no_namespace():
    xml = """
    <HamQTH version="2.7" >
        <session>
            <session_id>ABC123</session_id>
        </session>
    </HamQTH>
    """
    root = ET.fromstring(xml)

    element = _find_first_element(root, "session_id")

    assert element is not None
    assert element.text == "ABC123"
