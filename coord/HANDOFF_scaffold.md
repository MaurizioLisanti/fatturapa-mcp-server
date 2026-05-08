---
task_id: TASK_scaffold
status: DONE
timestamp: 2026-05-08T12:00:00+02:00
agent: claude-sonnet-4-6
---

## files_modified

- pyproject.toml
- Makefile
- Dockerfile
- docker-compose.yml
- .env.example
- .gitignore
- .gitleaks.toml
- CHANGELOG.md
- AGENTS.md
- SPEC.md
- README.md
- src/fatturapa_mcp/__init__.py
- src/fatturapa_mcp/server.py
- src/fatturapa_mcp/tools/__init__.py
- src/fatturapa_mcp/tools/validate.py
- src/fatturapa_mcp/tools/extract.py
- src/fatturapa_mcp/tools/sdi_errors.py
- src/fatturapa_mcp/tools/check_piva.py
- src/fatturapa_mcp/tools/vies.py
- src/fatturapa_mcp/schemas/README.md
- src/fatturapa_mcp/schemas/.gitkeep
- src/fatturapa_mcp/utils/__init__.py
- src/fatturapa_mcp/utils/logging.py
- tests/__init__.py
- tests/conftest.py
- tests/fixtures/valid_v13.xml
- tests/fixtures/valid_v12.xml
- tests/fixtures/invalid.xml
- tests/test_validate.py
- tests/test_extract.py
- tests/test_sdi_errors.py
- tests/test_check_piva.py
- tests/test_vies.py
- tests/test_logging.py
- coord/BOARD.md
- coord/STATE.json
- coord/DECISIONS.md
- .github/workflows/ci.yml

## tests_added

- tests/test_validate.py::TestValidateInvoiceSkeleton::test_raises_not_implemented_for_v13
- tests/test_validate.py::TestValidateInvoiceSkeleton::test_raises_not_implemented_for_v12
- tests/test_validate.py::TestValidateInvoiceSkeleton::test_raises_not_implemented_for_invalid
- tests/test_extract.py::TestExtractInvoiceDataSkeleton::test_raises_not_implemented_for_v13
- tests/test_extract.py::TestExtractInvoiceDataSkeleton::test_raises_not_implemented_for_v12
- tests/test_sdi_errors.py::TestLookupSdiErrorSkeleton::test_raises_not_implemented
- tests/test_sdi_errors.py::TestLookupSdiErrorSkeleton::test_raises_not_implemented_unknown_code
- tests/test_check_piva.py::TestCheckPivaSkeleton::test_raises_not_implemented
- tests/test_check_piva.py::TestCheckPivaSkeleton::test_raises_not_implemented_with_prefix
- tests/test_vies.py::TestVerifyPivaViesSkeleton::test_raises_not_implemented
- tests/test_vies.py::TestVerifyPivaViesSkeleton::test_raises_not_implemented_other_country
- tests/test_logging.py::TestMakeCorrelationId::test_returns_string
- tests/test_logging.py::TestMakeCorrelationId::test_returns_valid_uuid4
- tests/test_logging.py::TestMakeCorrelationId::test_each_call_returns_unique_id
- tests/test_logging.py::TestGetLoggerSkeleton::test_raises_not_implemented

## quality_gates

- ruff check: PASS (0 errors)
- ruff format: PASS (all files formatted)
- mypy: PASS (strict, 10 source files, 0 errors)
- pytest: PASS (15 passed, coverage: 100%)
- bandit: PASS (0 MEDIUM/HIGH findings)
- pip-audit: not run (network-dependent; run manually before release)

## notes

- Used `[project.optional-dependencies]` instead of PEP 735 `[dependency-groups]`
  because `pip install -e ".[dev]"` requires the former (see ADR-006).
- Added `[tool.coverage.run] omit = ["src/fatturapa_mcp/server.py"]` to exclude
  the MCP entry point from coverage; it wraps an external library call and is
  not unit-testable without integration setup.
- All skeleton tool functions raise `NotImplementedError`; skeleton tests verify
  this behaviour to achieve 100% coverage on the scaffold without business logic.
- `make_correlation_id()` is the one fully implemented function in the scaffold
  (a pure UUID4 wrapper with no external dependencies).
- Python runtime on this machine is 3.13; pyproject.toml targets 3.11. All
  checks passed on 3.13; CI matrix should pin 3.11 as specified.
- XSD schema files are not included; see `src/fatturapa_mcp/schemas/README.md`
  for download instructions.
