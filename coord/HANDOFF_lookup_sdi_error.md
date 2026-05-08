---
task_id: TASK_lookup_sdi_error
status: DONE
timestamp: 2026-05-08T14:10:00+02:00
agent: claude-sonnet-4-6
---

## files_modified

- src/fatturapa_mcp/tools/sdi_errors.py
- src/fatturapa_mcp/server.py
- tests/test_sdi_errors.py

## tests_added

- tests/test_sdi_errors.py::TestLookupSdiError::test_known_code_returns_all_keys
- tests/test_sdi_errors.py::TestLookupSdiError::test_struttura_code_00001
- tests/test_sdi_errors.py::TestLookupSdiError::test_struttura_code_00002
- tests/test_sdi_errors.py::TestLookupSdiError::test_contenuto_code_00101
- tests/test_sdi_errors.py::TestLookupSdiError::test_firma_code_00200
- tests/test_sdi_errors.py::TestLookupSdiError::test_firma_code_00202_scaduto
- tests/test_sdi_errors.py::TestLookupSdiError::test_recapito_code_00300
- tests/test_sdi_errors.py::TestLookupSdiError::test_duplicato_code_00115
- tests/test_sdi_errors.py::TestLookupSdiError::test_result_code_matches_input
- tests/test_sdi_errors.py::TestLookupSdiError::test_unknown_code_raises_value_error
- tests/test_sdi_errors.py::TestLookupSdiError::test_unknown_numeric_code_raises_value_error
- tests/test_sdi_errors.py::TestLookupSdiError::test_empty_string_raises_value_error

## quality_gates

- ruff check: PASS (0 errors)
- ruff format: PASS
- mypy: PASS (strict, 10 source files, 0 errors)
- pytest: PASS (62/62, coverage: sdi_errors.py 100%, overall 94.76%)
- bandit: PASS (0 MEDIUM/HIGH findings)

## notes

- Static table of 30 SDI error codes from AdE "Allegato C" spec.
- Four categories: STRUTTURA, CONTENUTO, FIRMA, RECAPITO.
- Unknown codes raise ValueError (not return a fallback dict) — callers can distinguish
  "code not in table" from "code found but invalid" at the application level.
- `LookupResult` TypedDict exported for downstream type checking.
- Tool registered in server.py via `mcp.tool()(lookup_sdi_error)`.
