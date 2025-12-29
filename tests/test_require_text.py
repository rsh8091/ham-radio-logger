import pytest
from hamqth_api import _require_text, HamQTHError


def test_require_text_good_string():
    good_call = "AG5XY"
    result = _require_text(good_call, "call sign")
    assert result == "AG5XY"


def test_require_text_white_space_included():
    call_with_spaces = "    AG5XY   "
    result = _require_text(call_with_spaces, "call sign")
    assert result == "AG5XY"


def test_require_text_all_spaces():
    all_spaces = "      "
    with pytest.raises(HamQTHError) as exc:
        _require_text(all_spaces, "call sign")

    assert "call sign" in str(exc.value).lower()


def test_require_text_none_value():
    with pytest.raises(HamQTHError) as exc:
        _require_text(None, "call sign")

    assert "call sign" in str(exc.value).lower()
