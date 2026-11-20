# HamQTH Lookup Checkpoint

November 19, 2026

## Working behavior

- Menu option 1 saves a confirmed QSO to `qsolog.jsonl`. Option 5 validates a callsign, looks it up in HamQTH, and prints the available fields one per line.
- The legacy XML client reuses a session ID for up to an hour. When HamQTH rejects a session, the client signs in again and retries the lookup once.
- The offline suite passed 44 tests, including a menu test that saves and looks up a callsign with simulated responses. The live `OK2CQR` test is skipped by default. An authenticated run and a JAWS walkthrough are pending.

## Credentials

Use temporary PowerShell environment variables for the current client, following the [README](../../README.md). Keep real credentials out of Git and local source files. The December 2025 notes record the move from hard-coded values to environment variables. This update used only test credentials.

## Next update

1. Move sign-in to [HamQTH API v2](https://www.hamqth.com/developers). Its HTTPS POST puts the password in the request body and subsequent lookups use a short-lived token. Prompt for the password when needed and keep the session token in memory.
2. Run the live `OK2CQR` test and try menu option 5 with JAWS.
3. Consider offering an optional lookup after the callsign prompt in option 1. Continue collecting QSO details if the lookup fails. Revisit result caching if repeat lookups become common.
