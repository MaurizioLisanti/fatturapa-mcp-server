---
task_id: TASK_roots_control
status: DONE
timestamp: 2026-05-20T09:51:00+02:00
agent: claude-sonnet-4-6
---

## files_modified
- src/fatturapa_mcp/utils/roots.py  (new)
- src/fatturapa_mcp/tools/validate.py
- src/fatturapa_mcp/tools/extract.py
- src/fatturapa_mcp/server.py
- tests/test_roots.py  (new)
- tests/test_validate.py
- tests/test_extract.py

## tests_added
- tests/test_roots.py::TestIsPathAllowed::test_path_inside_allowed_root_returns_true
- tests/test_roots.py::TestIsPathAllowed::test_path_outside_allowed_root_returns_false
- tests/test_roots.py::TestIsPathAllowed::test_path_traversal_attempt_returns_false
- tests/test_roots.py::TestIsPathAllowed::test_empty_roots_permits_any_path
- tests/test_roots.py::TestIsPathAllowed::test_relative_path_is_resolved_before_check
- tests/test_roots.py::TestIsPathAllowed::test_multiple_roots_matches_second
- tests/test_roots.py::TestIsPathAllowed::test_multiple_roots_no_match_returns_false
- tests/test_roots.py::TestIsPathAllowed::test_path_exactly_at_root_boundary_is_permitted
- tests/test_roots.py::TestIsPathAllowed::test_string_path_accepted
- tests/test_roots.py::TestGetAllowedRoots::test_empty_env_returns_empty_list
- tests/test_roots.py::TestGetAllowedRoots::test_blank_env_returns_empty_list
- tests/test_roots.py::TestGetAllowedRoots::test_single_path_parsed
- tests/test_roots.py::TestGetAllowedRoots::test_multiple_paths_parsed
- tests/test_roots.py::TestGetAllowedRoots::test_whitespace_around_paths_stripped
- tests/test_validate.py::TestValidateInvoiceFilePath::test_file_path_reads_and_validates
- tests/test_validate.py::TestValidateInvoiceFilePath::test_file_path_outside_roots_raises
- tests/test_validate.py::TestValidateInvoiceFilePath::test_neither_xml_nor_file_path_raises
- tests/test_extract.py::TestExtractInvoiceDataFilePath::test_file_path_reads_and_extracts
- tests/test_extract.py::TestExtractInvoiceDataFilePath::test_file_path_outside_roots_raises
- tests/test_extract.py::TestExtractInvoiceDataFilePath::test_neither_xml_nor_file_path_raises

## quality_gates
- ruff: PASS
- mypy: PASS (strict, 0 errors)
- pytest: PASS (121 tests, coverage: 97.06%)
- bandit: PASS (0 findings)

## notes
- `is_path_allowed` uses `Path.resolve()` on both the candidate and each root
  before calling `is_relative_to` — neutralises `..` traversal sequences and
  symlinks before any comparison.
- Empty `allowed_roots` → open mode (all paths permitted) for backward compat.
- Allowed roots are loaded from `FATTURAPA_ALLOWED_ROOTS` env var via
  `get_allowed_roots()`; paths are `os.pathsep`-separated.
- Both `validate_invoice` and `extract_invoice_data` gain an optional
  `file_path: str | None = None` parameter.  When provided, the roots check
  runs before any disk read; `PermissionError` is raised on denial.
- `xml_content` defaults to `""` so callers can supply only `file_path`.
  Calling with neither raises `ValueError`.
- `server.py` registers a `fatturapa://roots` resource via `@mcp.resource`
  that clients can query to discover the configured allowed paths.
- No path values are disclosed in log messages (only "Access denied" string).
