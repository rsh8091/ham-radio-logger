import os
import runpy
from pathlib import Path

import pytest

from hamqth_api import HamQTHError, callbook_lookup


@pytest.mark.skipif(
    os.getenv("HAMQTH_LIVE_TEST") != "1",
    reason="Set HAMQTH_LIVE_TEST=1 to query the live HamQTH callbook.",
)
def test_live_hamqth_lookup():
    logger_path = Path(__file__).resolve().parents[1] / "ham-radio-logger.py"
    prompt_for_credentials = runpy.run_path(str(logger_path))[
        "prompt_for_hamqth_credentials"
    ]
    try:
        result = callbook_lookup("OK2CQR", get_credentials=prompt_for_credentials)
    except HamQTHError as exc:
        raise pytest.fail.Exception(str(exc), pytrace=False) from None

    assert result["call_sign"] == "OK2CQR"
