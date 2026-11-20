import pytest

import hamqth_api


LOGIN = "<session><session_id>first-session</session_id></session>"
NEW_LOGIN = "<session><session_id>new-session</session_id></session>"
EXPIRED = "<session><error>Session does not exist or expired</error></session>"
FOUND = """
<search>
    <callsign>ag5xy</callsign>
    <nick> Randy </nick>
    <qth>Austin</qth>
    <us_state>TX</us_state>
    <country>United States</country>
    <cq>4</cq>
    <itu>7</itu>
</search>
"""


@pytest.fixture
def mock_hamqth(monkeypatch):
    monkeypatch.setenv("HAMQTH_USER", "testuser")
    monkeypatch.setenv("HAMQTH_PASS", "testpass")
    monkeypatch.setattr(hamqth_api, "_session", None)

    def set_responses(*responses):
        replies = iter(responses)
        requests = []

        def fake_http_get(url, params):
            assert url == "https://www.hamqth.com/xml.php"
            requests.append(params)
            return f'<HamQTH xmlns="https://www.hamqth.com">{next(replies)}</HamQTH>'

        monkeypatch.setattr(hamqth_api, "_http_get", fake_http_get)
        return requests

    return set_responses


def test_lookup_normalizes_callsign_and_reuses_session(mock_hamqth):
    requests = mock_hamqth(LOGIN, FOUND, "<search><callsign>k1abc/p</callsign></search>")

    assert hamqth_api.callbook_lookup(" ag5xy ") == {
        "call_sign": "AG5XY",
        "name": "Randy",
        "city": "Austin",
        "state": "TX",
        "country": "United States",
        "cq_zone": "4",
        "itu_zone": "7",
    }
    assert hamqth_api.callbook_lookup("k1abc/p") == {"call_sign": "K1ABC/P"}
    assert requests == [
        {"u": "testuser", "p": "testpass"},
        {"id": "first-session", "callsign": "AG5XY", "prg": "ham-radio-logger"},
        {"id": "first-session", "callsign": "K1ABC/P", "prg": "ham-radio-logger"},
    ]


def test_lookup_renews_session_after_an_hour(mock_hamqth, monkeypatch):
    times = iter([10, 3610])
    monkeypatch.setattr(hamqth_api, "monotonic", lambda: next(times))
    requests = mock_hamqth(LOGIN, FOUND, NEW_LOGIN, FOUND)

    hamqth_api.callbook_lookup("AG5XY")
    hamqth_api.callbook_lookup("AG5XY")

    assert requests[1]["id"] == "first-session"
    assert requests[3]["id"] == "new-session"


def test_lookup_retries_when_hamqth_rejects_session(mock_hamqth):
    requests = mock_hamqth(LOGIN, EXPIRED, NEW_LOGIN, FOUND)

    assert hamqth_api.callbook_lookup("AG5XY")["call_sign"] == "AG5XY"
    assert requests[1]["id"] == "first-session"
    assert requests[3]["id"] == "new-session"


def test_lookup_stops_after_second_session_rejection(mock_hamqth):
    requests = mock_hamqth(LOGIN, EXPIRED, NEW_LOGIN, EXPIRED)

    with pytest.raises(hamqth_api.HamQTHError, match="session"):
        hamqth_api.callbook_lookup("AG5XY")

    assert len(requests) == 4


@pytest.mark.parametrize("callsign", [" ", "AG5 XY", "AG5XY/", "CQ", "123"])
def test_lookup_rejects_invalid_input_before_network(mock_hamqth, callsign):
    requests = mock_hamqth()

    with pytest.raises(hamqth_api.HamQTHError, match="callsign"):
        hamqth_api.callbook_lookup(callsign)

    assert requests == []


def test_lookup_reports_missing_callsign_without_retrying(mock_hamqth):
    requests = mock_hamqth(LOGIN, "<session><error>Callsign not found</error></session>")

    with pytest.raises(hamqth_api.HamQTHError, match="AG5XY was not found"):
        hamqth_api.callbook_lookup("AG5XY")

    assert len(requests) == 2


@pytest.mark.parametrize("response", ["", "<search><callsign/></search>"])
def test_lookup_reports_unexpected_responses(mock_hamqth, response):
    mock_hamqth(LOGIN, response)

    with pytest.raises(hamqth_api.HamQTHError, match="Unexpected lookup response"):
        hamqth_api.callbook_lookup("AG5XY")
