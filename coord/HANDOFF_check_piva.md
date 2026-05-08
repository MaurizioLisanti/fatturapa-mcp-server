---
task_id: TASK_check_piva
status: DONE
timestamp: 2026-05-08T14:10:00+02:00
agent: claude-sonnet-4-6
---

## files_modified

- src/fatturapa_mcp/tools/check_piva.py
- src/fatturapa_mcp/server.py
- tests/test_check_piva.py

## tests_added

- tests/test_check_piva.py::TestCheckPiva::test_valid_piva_returns_true
- tests/test_check_piva.py::TestCheckPiva::test_valid_piva_normalised_field
- tests/test_check_piva.py::TestCheckPiva::test_strips_it_prefix_lowercase
- tests/test_check_piva.py::TestCheckPiva::test_strips_it_prefix_uppercase
- tests/test_check_piva.py::TestCheckPiva::test_strips_leading_trailing_whitespace
- tests/test_check_piva.py::TestCheckPiva::test_invalid_piva_wrong_check_digit
- tests/test_check_piva.py::TestCheckPiva::test_invalid_piva_reason_mentions_checksum
- tests/test_check_piva.py::TestCheckPiva::test_all_zeros_passes_checksum
- tests/test_check_piva.py::TestCheckPiva::test_too_short_returns_false
- tests/test_check_piva.py::TestCheckPiva::test_too_long_returns_false
- tests/test_check_piva.py::TestCheckPiva::test_non_digits_returns_false
- tests/test_check_piva.py::TestCheckPiva::test_empty_string_returns_false
- tests/test_check_piva.py::TestCheckPiva::test_only_prefix_returns_false
- tests/test_check_piva.py::TestCheckPiva::test_piva_field_stripped_on_invalid
- tests/test_check_piva.py::TestCheckPiva::test_piva_field_no_it_prefix_after_strip

## quality_gates

- ruff check: PASS (0 errors)
- ruff format: PASS
- mypy: PASS (strict, 0 errors)
- pytest: PASS (62/62, coverage: check_piva.py 100%)
- bandit: PASS (0 MEDIUM/HIGH findings)

## notes

- Implements the official MEF checksum algorithm:
  S_odd = sum of digits at positions 1,3,5,7,9 (1-indexed)
  S_even = sum of f(d) for d at positions 2,4,6,8,10 where f(d) = 2d if 2d<10 else 2d-9
  Valid iff (S_odd + S_even + D11) % 10 == 0
- "IT" prefix stripped case-insensitively; leading/trailing whitespace stripped.
- "00000000000" mathematically passes the checksum (all zeros → check digit = 0);
  semantic rejection of all-zeros is not in scope for a pure checksum validator.
- `CheckPivaResult` TypedDict exported; `reason` is str|None for mypy strictness.
- Tool registered in server.py via `mcp.tool()(check_piva)`.
