import pytest
import requests

from hamqth_api import _http_get, HamQTHError


class DummyResponse:
    def __init__(self, status_code=200, text="OK"):
        self.status_code = status_code
        self.text = text


def test_http_get_success(monkeypatch):
    def fake_get(url, params=None, timeout=None):
        return DummyResponse(status_code=200, text="<xml>success</xml>")

    monkeypatch.setattr(requests, "get", fake_get)

    result = _http_get("http://example.com", {"a": "b"})

    assert result == "<xml>success</xml>"


def test_http_get_non_200_raises(monkeypatch):
    def fake_get(url, params=None, timeout=None):
        return DummyResponse(status_code=500, text="Server error")

    monkeypatch.setattr(requests, "get", fake_get)

    with pytest.raises(HamQTHError) as exc:
        _http_get("http://example.com", {})

    assert "HTTP" in str(exc.value)


def test_http_get_network_error(monkeypatch):
    def fake_get(url, params=None, timeout=None):
        raise requests.exceptions.Timeout("Timed out")

    monkeypatch.setattr(requests, "get", fake_get)

    with pytest.raises(HamQTHError) as exc:
        _http_get("http://example.com", {})

    assert "network" in str(exc.value).lower()


def test_http_get_uses_timeout(monkeypatch):
    captured = {}

    def fake_get(url, params=None, timeout=None):
        captured["timeout"] = timeout
        return DummyResponse()

    monkeypatch.setattr(requests, "get", fake_get)

    _http_get("http://example.com", {})

    assert captured["timeout"] is not None
