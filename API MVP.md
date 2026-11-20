# MVP Overview — HamQTH Callsign Lookup

## Purpose
This document defines the **Minimum Viable Product (MVP)** for the HamQTH Python project.  
The goal is to keep scope tight, expectations clear, and development focused.

This MVP exists to answer one question well:

> “Can I look up a callsign from HamQTH and present it in a readable way?”

---

## Definition of Done (MVP)

The MVP is complete when:

- A user provides a callsign string
- The program:
  1. Validates the callsign
  2. Logs in to HamQTH if needed
  3. Performs a callsign lookup
  4. Parses the JSON response
  5. Prints a human-readable summary
- Common failures are handled gracefully:
  - invalid or missing credentials
  - expired or invalid session
  - callsign not found
  - network or parse errors

No persistence, no advanced caching, no UI polish.

---

## Input / Output Contract

### Input
- `callsign: str` (user-provided)

### Output (printed)
Screen-reader-friendly, label-per-line format:

Callsign: AG5XY
Name: <if present>
QTH: <city/state if present>
Country: <if present>


Notes:
- Fields are optional
- Missing fields are omitted
- No tables or fancy formatting

---

## MVP Components

### Implemented

- The API module handles callsign validation, HTTP timeouts, and HamQTH v2 JSON responses.
- The module keeps the session token in memory for up to one hour. If HamQTH rejects it, the lookup prompts for sign-in again and retries once.
- `callbook_lookup()` returns a dictionary. `format_callbook_result()` prints the available fields from menu option 5.
- Menu option 1 saves QSOs to the local JSONL log. Lookups run separately through option 5.

### Live verification

- November 20, 2026. Randy confirmed that option 5 returned live callsign results with his HamQTH account.
- The opt-in `OK2CQR` pytest test is available for a repeatable live check.

---

## Explicitly Out of Scope for MVP

The following are **not** part of the MVP:

- Saving results to disk
- Logger / QSO integration
- Bulk or batch lookups
- Rich formatting (tables, colors)
- Aggressive caching or rate limiting
- Multiple callbook providers

These can be added **after** the MVP works end-to-end.

---

## Testing Philosophy

- All helpers are developed **test-first**
- The regular suite uses mocked network responses. The live lookup test runs only when explicitly enabled.
- JSON fixtures model HamQTH responses and HTTP status codes
- Helpers do one thing and return simple values
- Errors are translated into `HamQTHError` with friendly messages

---

## Future logger refactor:

- Existing logger currently saves/loads JSON.
- Randy already uses another ham log format.
- Keep HamQTH lookup output format-neutral.
- Later add import/export adapters for the real logging format.
- Do not mix callbook lookup logic with log persistence.

## Timeline Expectation

We are working on this as we can. So the old timeline no longer applies. That timeline was when my current job was starting

---

## Durable Context for Future Sessions

If chat context is lost, this MVP file plus the test suite is sufficient to resume work.

One-line context summary:

> The Windows terminal logger supports local QSO logging and standalone HamQTH v2 lookup. The offline tests pass, and a live lookup through option 5 succeeded. See the [project checkpoint](docs/notes/2026-11-19-hamqth-lookup-checkpoint.md) for the next update.

