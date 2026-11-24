import datetime
import getpass
import json
import runpy
import warnings
from pathlib import Path
from types import SimpleNamespace

import pytest
import requests

import hamqth_api


LOGGER = Path(__file__).resolve().parents[1] / "ham-radio-logger.py"


def test_new_qso_keeps_utc_start_time_alongside_legacy_entries(
    monkeypatch, tmp_path, capsys
):
    old_qso = {"call_sign": "W1AW", "band": "40M", "comments": "Old entry"}
    log_path = tmp_path / "qsolog.jsonl"
    log_path.write_text(json.dumps(old_qso) + "\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    now = datetime.datetime(2026, 11, 20, 23, 59, 58, tzinfo=datetime.timezone.utc)
    after_midnight = now + datetime.timedelta(seconds=5)

    class TestClock(datetime.datetime):
        @classmethod
        def now(cls, tz=None):
            assert tz == datetime.timezone.utc
            return now

    entries = iter(
        [
            "1", "k1abc", "", "59", "57", "20m", "", "ssb", "Good contact", "y",
            "2", "2", "6",
        ]
    )

    def enter_value(prompt=""):
        nonlocal now
        value = next(entries)
        if value == "k1abc":
            now = after_midnight
        return value

    monkeypatch.setattr(datetime, "datetime", TestClock)
    monkeypatch.setattr("builtins.input", enter_value)

    runpy.run_path(str(LOGGER), run_name="__main__")

    existing, new = [
        json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()
    ]
    assert existing == old_qso
    assert new["qso_date"] == "2026-11-20"
    assert new["time_on"] == "23:59:58"
    assert new["comments"] == "Good contact"
    assert "frequency_mhz" not in new
    output = capsys.readouterr().out
    assert "Call Sign: W1AW" in output
    assert output.count("QSO date (UTC): 2026-11-20") == 2
    assert output.count("Start time (UTC): 23:59:58") == 2


def test_new_qso_saves_manual_frequency_in_mhz(monkeypatch, tmp_path, capsys):
    entries = iter(
        [
            "1", "k1abc", "", "59", "57", "20m", "-14", "NaN", "0", "14.074050",
            "ssb", "", "y", "6",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda prompt="": next(entries))
    monkeypatch.chdir(tmp_path)

    runpy.run_path(str(LOGGER), run_name="__main__")

    saved_qso = json.loads((tmp_path / "qsolog.jsonl").read_text(encoding="utf-8"))
    assert saved_qso["band"] == "20M"
    assert saved_qso["frequency_mhz"] == "14.074050"
    assert saved_qso["mode"] == "SSB"
    output = capsys.readouterr().out
    assert "Frequency (MHz): 14.074050" in output
    assert output.count("Enter a positive frequency in MHz") == 3
    assert "QSO saved" in output


def test_menu_can_log_and_look_up_callsigns(monkeypatch, tmp_path, capsys):
    entries = iter(
        [
            "1", "k1abc", "", "59", "57", "20m", "", "ssb", "", "y",
            "5", "k1abc", " ag5xy ", "6",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda prompt="": next(entries))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(hamqth_api, "_session", None)
    monkeypatch.setattr(getpass, "getpass", lambda prompt: "test password")

    def fake_request(method, url, **kwargs):
        assert (tmp_path / "qsolog.jsonl").read_text(encoding="utf-8")
        if method == "POST":
            assert kwargs["json"] == {"callsign": "AG5XY", "password": "test password"}
            payload = {"token": "abc123", "expiresIn": 3600}
        else:
            assert url.endswith("/callbook/K1ABC")
            payload = {
                "callsign": "k1abc",
                "nick": "Pat",
                "qth": "Boston",
                "region": {"usState": "MA"},
                "country": None,
            }
        return SimpleNamespace(status_code=200, json=lambda: payload)

    monkeypatch.setattr(requests, "request", fake_request)

    runpy.run_path(str(LOGGER), run_name="__main__")

    output = capsys.readouterr().out
    assert "QSO saved" in output
    assert "Callsign: K1ABC\nName: Pat\nQTH: Boston, MA\n" in output
    assert "Country:" not in output
    assert "test password" not in output and "abc123" not in output
    assert "Goodbye and 73!" in output
    saved_qso = json.loads((tmp_path / "qsolog.jsonl").read_text(encoding="utf-8"))
    assert saved_qso["call_sign"] == "K1ABC"
    assert saved_qso["band"] == "20M"
    assert saved_qso["mode"] == "SSB"


@pytest.mark.parametrize(
    ("reply", "expected_line"),
    [
        (
            {
                "call_sign": "K1ABC",
                "city": "Boston",
                "state": "MA",
                "country": "United States",
            },
            "QTH: Boston, MA, United States",
        ),
        (
            {"call_sign": "K1ABC"},
            "HamQTH has no QTH listed for this station.",
        ),
        (
            hamqth_api.HamQTHError("Network error contacting HamQTH."),
            "Network error contacting HamQTH.",
        ),
    ],
)
def test_optional_qth_lookup_continues_logging(
    monkeypatch, tmp_path, capsys, reply, expected_line
):
    entries = iter(["1", "k1abc", "y", "59", "57", "20m", "", "ssb", "", "y", "6"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(entries))
    monkeypatch.chdir(tmp_path)

    def fake_lookup(callsign, *, get_credentials):
        assert callsign.upper() == "K1ABC"
        if isinstance(reply, hamqth_api.HamQTHError):
            raise reply
        return reply

    monkeypatch.setattr(hamqth_api, "callbook_lookup", fake_lookup)

    runpy.run_path(str(LOGGER), run_name="__main__")

    output = capsys.readouterr().out
    assert expected_line in output
    assert output.index(expected_line) < output.index("Enter signal report")
    assert "QSO saved" in output
    saved_qso = json.loads((tmp_path / "qsolog.jsonl").read_text(encoding="utf-8"))
    assert saved_qso["call_sign"] == "K1ABC"
    assert saved_qso["their_signal_report"] == "59"
    assert not saved_qso.keys() & {"city", "state", "country", "qth"}


def test_lookup_failure_returns_to_main_menu(monkeypatch, tmp_path, capsys):
    entries = iter(["5", "k1abc", "6"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(entries))
    monkeypatch.chdir(tmp_path)

    def failed_lookup(callsign, *, get_credentials):
        raise hamqth_api.HamQTHError("Network error contacting HamQTH.")

    monkeypatch.setattr(hamqth_api, "callbook_lookup", failed_lookup)

    runpy.run_path(str(LOGGER), run_name="__main__")

    output = capsys.readouterr().out
    assert "Network error contacting HamQTH." in output
    assert output.count("Ham Radio Logger - Main Menu") == 2
    assert "Goodbye and 73!" in output


@pytest.mark.parametrize(
    ("username", "password", "message"),
    [
        ("", None, "HamQTH sign-in canceled."),
        ("AG5XY", "", "HamQTH sign-in canceled."),
        ("AG5XY", None, "Cannot hide password input"),
    ],
)
def test_sign_in_cancel_or_unmasked_console_returns_to_menu(
    monkeypatch, tmp_path, capsys, username, password, message
):
    entries = iter(["5", "k1abc", username, "6"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(entries))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(hamqth_api, "_session", None)

    def read_password(prompt):
        assert username
        if password is None:
            warnings.warn("Password input may be echoed.", getpass.GetPassWarning)
            pytest.fail("The unmasked password prompt should stop at the warning.")
        return password

    def unexpected_request(*args, **kwargs):
        pytest.fail("A canceled sign-in must not call HamQTH.")

    monkeypatch.setattr(getpass, "getpass", read_password)
    monkeypatch.setattr(requests, "request", unexpected_request)

    runpy.run_path(str(LOGGER), run_name="__main__")

    output = capsys.readouterr().out
    assert message in output
    assert "Goodbye and 73!" in output
