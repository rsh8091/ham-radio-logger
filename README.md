# ham-radio-logger

A Python terminal app for logging amateur radio QSOs and looking up callsigns in HamQTH. It prints one labeled field per line for screen readers.

## Run the logger in PowerShell

On a fresh checkout, create the virtual environment and install the dependencies from the project folder.

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Start the logger from the same folder.

```powershell
.\venv\Scripts\python.exe .\ham-radio-logger.py
```

Choose **1** to log a QSO, **2** to list recent QSOs, or **3** to search the local log. The logger saves confirmed entries in `qsolog.jsonl` in the current folder.

Option **1** captures the date and time in UTC when you start the entry and shows both in the review before saving.

Option **5** uses your HamQTH account. Use your callsign as the username. If you need an account, select **Join us** on the [HamQTH sign-in page](https://www.hamqth.com/login).

Choose **5** and enter `OK2CQR` to try a lookup. When sign-in is needed, enter your own callsign and then your password. The password prompt keeps your typing hidden. Press **Enter** at an empty sign-in prompt to return to the menu.

The logger sends the password to HamQTH API v2 over HTTPS and keeps the session token in memory for up to an hour. Keep real credentials out of Git, source files, and `.env` files.

Lookup results include the supported fields HamQTH has available for that callsign. A valid result may only include a few fields.

## Run tests

```powershell
.\venv\Scripts\python.exe -m pytest -q
```

The regular tests use simulated HamQTH responses and a temporary QSO log. They skip the live test by default.

### Test a live callsign lookup

Run this in an interactive PowerShell terminal. The test uses the logger's sign-in prompts and checks that HamQTH returns `OK2CQR`. The `-s` flag lets the prompts use your terminal.

```powershell
$env:HAMQTH_LIVE_TEST = '1'
.\venv\Scripts\python.exe -m pytest -q -s tests/test_hamqth_live.py
Remove-Item Env:HAMQTH_LIVE_TEST
```

