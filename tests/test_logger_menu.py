import json
import runpy
from pathlib import Path

import hamqth_api


LOGGER = Path(__file__).resolve().parents[1] / "ham-radio-logger.py"


def test_menu_can_log_and_look_up_callsigns(monkeypatch, tmp_path, capsys):
    entries = iter(["1", "k1abc", "59", "57", "20m", "ssb", "", "y", "5", "k1abc", "6"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(entries))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HAMQTH_USER", "testuser")
    monkeypatch.setenv("HAMQTH_PASS", "testpass")
    monkeypatch.setattr(hamqth_api, "_session", None)

    def fake_http_get(url, params):
        if "u" in params:
            return "<HamQTH><session><session_id>abc123</session_id></session></HamQTH>"
        assert params["callsign"] == "K1ABC"
        return """<HamQTH xmlns="https://www.hamqth.com">
            <search>
                <callsign>k1abc</callsign><nick>Pat</nick>
                <qth>Boston</qth><us_state>MA</us_state><country> </country>
            </search>
        </HamQTH>"""

    monkeypatch.setattr(hamqth_api, "_http_get", fake_http_get)

    runpy.run_path(str(LOGGER), run_name="__main__")

    output = capsys.readouterr().out
    assert "QSO saved" in output
    assert "Callsign: K1ABC\nName: Pat\nQTH: Boston, MA\n" in output
    assert "Country:" not in output
    assert "Goodbye and 73!" in output
    saved_qso = json.loads((tmp_path / "qsolog.jsonl").read_text(encoding="utf-8"))
    assert saved_qso["call_sign"] == "K1ABC"
    assert saved_qso["band"] == "20M"
    assert saved_qso["mode"] == "SSB"


def test_lookup_failure_returns_to_main_menu(monkeypatch, tmp_path, capsys):
    entries = iter(["5", "k1abc", "6"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(entries))
    monkeypatch.chdir(tmp_path)

    def failed_lookup(callsign):
        raise hamqth_api.HamQTHError("Network error contacting HamQTH.")

    monkeypatch.setattr(hamqth_api, "callbook_lookup", failed_lookup)

    runpy.run_path(str(LOGGER), run_name="__main__")

    output = capsys.readouterr().out
    assert "Network error contacting HamQTH." in output
    assert output.count("Ham Radio Logger - Main Menu") == 2
    assert "Goodbye and 73!" in output
