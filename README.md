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

Option **5** uses your HamQTH account. Use your callsign as the username. If you need an account, select **Join us** on the [HamQTH sign-in page](https://www.hamqth.com/login).

Set the credentials in the current PowerShell session. The prompt keeps your password out of command history. Keep real credentials out of Git, source files, and `.env` files.

```powershell
$hamQthCredential = Get-Credential -Message 'Enter your HamQTH username and password'
$env:HAMQTH_USER = $hamQthCredential.UserName
$env:HAMQTH_PASS = $hamQthCredential.GetNetworkCredential().Password
Remove-Variable hamQthCredential
```

Start the logger from that session, choose **5**, and enter `OK2CQR` to try a lookup. When you finish using HamQTH, close the PowerShell session or clear both variables.

```powershell
Remove-Item Env:HAMQTH_USER, Env:HAMQTH_PASS
```

## Run tests

```powershell
.\venv\Scripts\python.exe -m pytest -q
```

The regular tests use simulated HamQTH responses and a temporary QSO log. They skip the live test by default.

### Test a live callsign lookup

After setting `HAMQTH_USER` and `HAMQTH_PASS` as shown above, run this in the same PowerShell session. The test signs in to HamQTH and checks that the service returns `OK2CQR`.

```powershell
$env:HAMQTH_LIVE_TEST = '1'
.\venv\Scripts\python.exe -m pytest -q tests/test_hamqth_live.py
Remove-Item Env:HAMQTH_LIVE_TEST
```

