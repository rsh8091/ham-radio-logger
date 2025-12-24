# Ham Radio Logger – Project Runbook

## Project Goal
Build a beginner-friendly ham radio logging application that:
- Logs QSOs locally
- Supports search, stats, and display
- Gradually integrates external callbook APIs (starting with **HamQTH**)
- Is testable, maintainable, and easy to reason about

This project is intentionally incremental and educational.

---

## Current Architecture (High Level)

### CLI / Main Logic
- Handles user interaction
- Calls helper functions for logging, search, stats
- Will call API functions (no API logic lives in the CLI)

### HamQTH API Module (`hamqth_api.py`)
- Owns *all* HamQTH behavior:
  - credentials
  - session handling
  - HTTP requests
  - XML parsing
- Exposes a small public interface
- Raises `HamQTHError` with user-friendly messages
- Contains internal helper functions, developed one at a time

### Tests
- Written with `pytest`
- Focus on small, deterministic helper functions first
- Environment variables are isolated in tests

---

## Environment Variables

The HamQTH API module expects credentials via environment variables:

- `HAMQTH_USER`
- `HAMQTH_PASS`

These must be set before making any API calls.

Credentials are **never** hard-coded in the source.

---

## Testing

### Test Framework
- `pytest`
- Tests live in the `tests/` directory
- Test discovery is locked down via `pytest.ini`

### Running Tests
From repo root, with the virtual environment activated:

```powershell
python -m pytest -q
