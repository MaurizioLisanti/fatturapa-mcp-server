---
task_id: TASK_verify_piva_vies
status: DONE
timestamp: 2026-05-08T14:10:00+02:00
agent: claude-sonnet-4-6
---

## files_modified

- src/fatturapa_mcp/tools/vies.py
- src/fatturapa_mcp/server.py
- tests/test_vies.py
- pyproject.toml  (added pytest-httpx>=0.30.0 to dev deps)

## tests_added

- tests/test_vies.py::TestVerifyPivaVies::test_valid_vat_returns_true
- tests/test_vies.py::TestVerifyPivaVies::test_invalid_vat_returns_false
- tests/test_vies.py::TestVerifyPivaVies::test_undisclosed_name_returns_none
- tests/test_vies.py::TestVerifyPivaVies::test_undisclosed_address_returns_none
- tests/test_vies.py::TestVerifyPivaVies::test_non_it_country
- tests/test_vies.py::TestVerifyPivaVies::test_country_code_uppercased
- tests/test_vies.py::TestVerifyPivaVies::test_timeout_returns_unavailable
- tests/test_vies.py::TestVerifyPivaVies::test_connection_error_returns_unavailable
- tests/test_vies.py::TestVerifyPivaVies::test_http_500_returns_unavailable
- tests/test_vies.py::TestVerifyPivaVies::test_missing_is_valid_field_defaults_false

## quality_gates

- ruff check: PASS (0 errors)
- ruff format: PASS
- mypy: PASS (strict, 0 errors)
- pytest: PASS (62/62, coverage: vies.py 100%, overall 94.76%)
- bandit: PASS (0 MEDIUM/HIGH findings)

## notes

- Endpoint: https://ec.europa.eu/taxation_customs/vies/rest-api/ms/{cc}/vat/{vat}
  (EU VIES REST API v2; GET, returns JSON).
- country_code is .upper()-ed before building the URL so callers can pass "it" or "IT".
- VIES returns "---" when the member state does not disclose name/address; these map to None.
- Any httpx.HTTPError, httpx.TimeoutException, or JSON parse ValueError returns
  source="unavailable", valid=False — never raises to the MCP layer.
- Timeout hardcoded at 10 s (_TIMEOUT_SECONDS); httpx.AsyncClient used as async context manager.
- Tests use pytest-httpx HTTPXMock fixture (added to dev deps).
- Tool registered in server.py via `mcp.tool()(verify_piva_vies)`.
