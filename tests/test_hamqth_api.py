import pytest

from hamqth_api import HamQTHError, _load_credentials


def test_load_credentials_returns_stripped_values(monkeypatch):
    monkeypatch.setenv("HAMQTH_USER", "  bob  ")
    monkeypatch.setenv("HAMQTH_PASS", "  123  ")

    user, pw = _load_credentials()

    assert user == "bob"
    assert pw == "123"


def test_load_credentials_raises_if_user_missing(monkeypatch):
    monkeypatch.delenv("HAMQTH_USER", raising=False)
    monkeypatch.setenv("HAMQTH_PASS", "123")

    with pytest.raises(HamQTHError) as excinfo:
        _load_credentials()

    assert "HAMQTH_USER" in str(excinfo.value)
    assert "HAMQTH_PASS" in str(excinfo.value)


def test_load_credentials_raises_if_pass_missing(monkeypatch):
    monkeypatch.setenv("HAMQTH_USER", "bob")
    monkeypatch.delenv("HAMQTH_PASS", raising=False)

    with pytest.raises(HamQTHError) as excinfo:
        _load_credentials()

    assert "HAMQTH_USER" in str(excinfo.value)
    assert "HAMQTH_PASS" in str(excinfo.value)


def test_load_credentials_raises_if_blank_values(monkeypatch):
    monkeypatch.setenv("HAMQTH_USER", "   ")
    monkeypatch.setenv("HAMQTH_PASS", "")

    with pytest.raises(HamQTHError):
        _load_credentials()
