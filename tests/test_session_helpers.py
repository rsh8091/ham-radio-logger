from hamqth_api import (
    _is_session_error,
    _is_not_found_error,
    _extract_session_id,
    _parse_xml,
)


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
