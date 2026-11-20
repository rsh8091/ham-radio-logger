import os

import pytest

from hamqth_api import HamQTHError, callbook_lookup


@pytest.mark.skipif(
    os.getenv("HAMQTH_LIVE_TEST") != "1",
    reason="Set HAMQTH_LIVE_TEST=1 to query the live HamQTH callbook.",
)
def test_live_hamqth_lookup():
    try:
        result = callbook_lookup("OK2CQR")
    except HamQTHError as exc:
        # A chained network exception can include the login URL and its credentials.
        raise pytest.fail.Exception(str(exc), pytrace=False) from None

    assert result["call_sign"] == "OK2CQR"
