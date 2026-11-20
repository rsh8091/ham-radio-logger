import json
from unittest.mock import Mock

import pytest
import requests

import hamqth_api


BASE_URL = "https://www.hamqth.com/api/v2"
LOGIN = (200, {"token": "first-token", "expiresIn": 120})
NEW_LOGIN = (200, {"token": "new-token", "expiresIn": 3600})
EXPIRED = (401, {"detail": "Expired token"})
FOUND = (
    200,
    {
        "callsign": "ag5xy",
        "nick": " Randy ",
        "name": "Full name",
        "qth": "Austin",
        "region": {"usState": "TX"},
        "country": "United States",
        "cq": 4,
        "itu": 7,
    },
)


@pytest.fixture
def credentials():
    return Mock(return_value=("AG5XY", " test password "))


@pytest.fixture
def mock_hamqth(monkeypatch):
    monkeypatch.setattr(hamqth_api, "_session", None)

    def set_responses(*responses):
        replies = iter(responses)
        calls = []

        def fake_request(method, url, *, timeout, allow_redirects, **kwargs):
            assert timeout == 10
            assert allow_redirects is False
            calls.append((method, url, kwargs))
            status, body = next(replies)
            response = requests.Response()
            response.status_code = status
            response._content = (
                body if isinstance(body, bytes) else json.dumps(body).encode()
            )
            return response

        monkeypatch.setattr(requests, "request", fake_request)
        return calls

    return set_responses


def test_lookup_uses_json_and_only_sends_password_in_login_body(
    mock_hamqth, credentials
):
    portable = (200, {"callsign": "k1abc", "nick": " ", "region": None})
    calls = mock_hamqth(LOGIN, FOUND, portable)

    assert hamqth_api.callbook_lookup(" ag5xy ", get_credentials=credentials) == {
        "call_sign": "AG5XY",
        "name": "Randy",
        "city": "Austin",
        "state": "TX",
        "country": "United States",
        "cq_zone": "4",
        "itu_zone": "7",
    }
    assert hamqth_api.callbook_lookup("k1abc/p", get_credentials=credentials) == {
        "call_sign": "K1ABC",
    }
    credentials.assert_called_once_with()
    assert calls == [
        (
            "POST",
            f"{BASE_URL}/login",
            {"json": {"callsign": "AG5XY", "password": " test password "}},
        ),
        (
            "GET",
            f"{BASE_URL}/callbook/AG5XY",
            {
                "headers": {"Authorization": "Bearer first-token"},
                "params": {"app": "ham-radio-logger"},
            },
        ),
        (
            "GET",
            f"{BASE_URL}/callbook/K1ABC%2FP",
            {
                "headers": {"Authorization": "Bearer first-token"},
                "params": {"app": "ham-radio-logger"},
            },
        ),
    ]


def test_lookup_uses_expiry_returned_by_server(mock_hamqth, credentials, monkeypatch):
    now = 10
    monkeypatch.setattr(hamqth_api, "monotonic", lambda: now)
    calls = mock_hamqth(LOGIN, FOUND, FOUND, NEW_LOGIN, FOUND)

    hamqth_api.callbook_lookup("AG5XY", get_credentials=credentials)
    now = 129
    hamqth_api.callbook_lookup("AG5XY", get_credentials=credentials)
    now = 130
    hamqth_api.callbook_lookup("AG5XY", get_credentials=credentials)

    assert [method for method, _, _ in calls] == ["POST", "GET", "GET", "POST", "GET"]
    assert credentials.call_count == 2
    assert calls[-1][2]["headers"] == {"Authorization": "Bearer new-token"}


def test_lookup_retries_when_hamqth_rejects_token(mock_hamqth, credentials):
    calls = mock_hamqth(LOGIN, EXPIRED, NEW_LOGIN, FOUND)

    result = hamqth_api.callbook_lookup("AG5XY", get_credentials=credentials)
    assert result["call_sign"] == "AG5XY"
    assert credentials.call_count == 2
    assert calls[1][2]["headers"] == {"Authorization": "Bearer first-token"}
    assert calls[3][2]["headers"] == {"Authorization": "Bearer new-token"}


def test_lookup_stops_after_second_token_rejection(mock_hamqth, credentials):
    calls = mock_hamqth(LOGIN, EXPIRED, NEW_LOGIN, EXPIRED)

    with pytest.raises(hamqth_api.HamQTHError, match="rejected the session"):
        hamqth_api.callbook_lookup("AG5XY", get_credentials=credentials)

    assert len(calls) == 4


@pytest.mark.parametrize("callsign", [" ", "AG5 XY", "AG5XY/", "CQ", "123"])
def test_lookup_rejects_invalid_input_before_asking_for_credentials(
    mock_hamqth, credentials, callsign
):
    calls = mock_hamqth()

    with pytest.raises(hamqth_api.HamQTHError, match="callsign"):
        hamqth_api.callbook_lookup(callsign, get_credentials=credentials)

    credentials.assert_not_called()
    assert calls == []


@pytest.mark.parametrize(
    ("status", "message"),
    [
        (401, "callsign or password"),
        (429, "too many sign-in attempts"),
        (307, "status 307"),
    ],
)
def test_login_errors_do_not_retry_or_display_response_data(
    mock_hamqth, credentials, status, message
):
    calls = mock_hamqth((status, {"detail": " test password "}))

    with pytest.raises(hamqth_api.HamQTHError, match=message) as error:
        hamqth_api.callbook_lookup("AG5XY", get_credentials=credentials)

    assert "test password" not in str(error.value)
    assert len(calls) == 1


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"token": "", "expiresIn": 3600},
        {"token": "token", "expiresIn": 0},
        {"token": "token", "expiresIn": True},
    ],
)
def test_login_requires_a_token_and_valid_expiry(mock_hamqth, credentials, body):
    mock_hamqth((200, body))

    with pytest.raises(hamqth_api.HamQTHError, match="Unexpected sign-in response"):
        hamqth_api.callbook_lookup("AG5XY", get_credentials=credentials)


@pytest.mark.parametrize(
    ("status", "message"),
    [(404, "AG5XY was not found"), (503, "status 503")],
)
def test_lookup_http_errors_do_not_retry(mock_hamqth, credentials, status, message):
    calls = mock_hamqth(LOGIN, (status, {}))

    with pytest.raises(hamqth_api.HamQTHError, match=message):
        hamqth_api.callbook_lookup("AG5XY", get_credentials=credentials)

    assert len(calls) == 2


@pytest.mark.parametrize(
    ("body", "message"),
    [
        (b"invalid-json", "Invalid JSON"),
        ([], "Expected a JSON object"),
        ({}, "No callsign found"),
    ],
)
def test_lookup_reports_unexpected_responses(mock_hamqth, credentials, body, message):
    mock_hamqth(LOGIN, (200, body))

    with pytest.raises(hamqth_api.HamQTHError, match=message):
        hamqth_api.callbook_lookup("AG5XY", get_credentials=credentials)


def test_network_errors_hide_request_details(mock_hamqth, credentials, monkeypatch):
    def time_out(*args, **kwargs):
        raise requests.exceptions.Timeout("sensitive request details")

    monkeypatch.setattr(requests, "request", time_out)

    with pytest.raises(
        hamqth_api.HamQTHError, match="Network error contacting HamQTH"
    ) as error:
        hamqth_api.callbook_lookup("AG5XY", get_credentials=credentials)

    assert error.value.__suppress_context__
