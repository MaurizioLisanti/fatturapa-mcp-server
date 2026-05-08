---
task_id: TASK_validate_invoice
status: DONE
timestamp: 2026-05-08T12:15:00+02:00
agent: Claude Code
---

## files_modified

- src/fatturapa_mcp/tools/validate.py
- src/fatturapa_mcp/schemas/FatturaPA_v1.2.xsd
- src/fatturapa_mcp/schemas/FatturaPA_v1.3.xsd
- tests/test_validate.py

## tests_added

- tests/test_validate.py::TestValidateInvoice::test_valid_v13_passes
- tests/test_validate.py::TestValidateInvoice::test_valid_v12_passes
- tests/test_validate.py::TestValidateInvoice::test_malformed_xml_fails
- tests/test_validate.py::TestValidateInvoice::test_unknown_namespace_fails
- tests/test_validate.py::TestValidateInvoice::test_xsd_structural_violation_fails
- tests/test_validate.py::TestValidateInvoice::test_xsd_not_found

## quality_gates

- ruff: PASS
- mypy: PASS
- pytest: 18/18
- bandit: PASS
- coverage: 100%

## notes

XSD stubs v1.2 + v1.3, auto-detect namespace, 6 contract tests
