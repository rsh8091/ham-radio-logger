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
  4. Parses the XML response
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

### Already Implemented
- `_http_get()` — network boundary with timeout and error handling
- `_parse_xml()` — XML parsing with exception translation
- `_require_text()` — input validation and normalization
- Pytest infrastructure working on Windows
- Tests do not hit the network

---

### To Implement (In Order)

1. **XML interpretation helpers**
   - `_extract_error_message(root)`
   - `_is_session_error(msg)`
   - `_is_not_found_error(msg)`
   - `_extract_session_id(root)`

2. **Session handling (minimal)**
   - `_login_and_create_session()`
   - `_get_session_id()`
     - cache session id
     - track expiry
     - retry login once if session error occurs

3. **Lookup orchestration**
   - `callbook_lookup(callsign)`
     - validate input
     - obtain session id
     - perform lookup
     - handle errors
     - return parsed result as a dict

4. **Formatting**
   - `format_callbook_result(result: dict) -> str`
   - converts lookup result into readable output

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
- Network calls are always mocked
- XML samples are small and hand-written
- Helpers do one thing and return simple values
- Errors are translated into `HamQTHError` with friendly messages

---

## Timeline Expectation

With focused sessions, this MVP is realistic to complete **within one work week**:

- Day 1: XML helpers + session ID extraction
- Day 2: Session lifecycle (login, cache, retry)
- Day 3: `callbook_lookup()` happy path + errors
- Day 4: Formatting + CLI wiring + cleanup

---

## Durable Context for Future Sessions

If chat context is lost, this MVP file plus the test suite is sufficient to resume work.

One-line context summary:

> We are building a test-first Python HamQTH callsign lookup MVP on Windows. HTTP, XML parsing, and input validation helpers are complete and tested. Next we are implementing XML error/session helpers, minimal session handling, and readable callsign output.

