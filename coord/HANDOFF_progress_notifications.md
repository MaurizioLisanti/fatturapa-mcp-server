---
task_id: TASK_progress_notifications
status: DONE
timestamp: 2026-05-20T09:03:00+02:00
agent: claude-sonnet-4-6
---

## files_modified
- src/fatturapa_mcp/tools/validate.py
- src/fatturapa_mcp/tools/extract.py
- src/fatturapa_mcp/tools/sdi_errors.py
- src/fatturapa_mcp/tools/check_piva.py
- src/fatturapa_mcp/tools/vies.py
- tests/conftest.py
- tests/test_validate.py
- tests/test_extract.py
- tests/test_sdi_errors.py
- tests/test_check_piva.py
- tests/test_vies.py

## tests_added
- tests/test_validate.py::TestValidateInvoiceProgress::test_valid_invoice_emits_three_steps
- tests/test_validate.py::TestValidateInvoiceProgress::test_malformed_xml_emits_only_first_step
- tests/test_validate.py::TestValidateInvoiceProgress::test_no_ctx_does_not_raise
- tests/test_extract.py::TestExtractInvoiceDataProgress::test_happy_path_emits_three_steps
- tests/test_extract.py::TestExtractInvoiceDataProgress::test_no_ctx_does_not_raise
- tests/test_sdi_errors.py::TestLookupSdiErrorProgress::test_known_code_emits_three_steps
- tests/test_sdi_errors.py::TestLookupSdiErrorProgress::test_unknown_code_emits_only_first_step
- tests/test_sdi_errors.py::TestLookupSdiErrorProgress::test_no_ctx_does_not_raise
- tests/test_check_piva.py::TestCheckPivaProgress::test_valid_piva_emits_three_steps
- tests/test_check_piva.py::TestCheckPivaProgress::test_format_error_emits_only_first_step
- tests/test_check_piva.py::TestCheckPivaProgress::test_wrong_length_emits_only_first_step
- tests/test_check_piva.py::TestCheckPivaProgress::test_no_ctx_does_not_raise
- tests/test_vies.py::TestVerifyPivaViesProgress::test_valid_response_emits_four_steps
- tests/test_vies.py::TestVerifyPivaViesProgress::test_network_error_emits_two_steps
- tests/test_vies.py::TestVerifyPivaViesProgress::test_no_ctx_does_not_raise

## quality_gates
- ruff: PASS
- mypy: PASS (strict, 0 errors)
- pytest: PASS (101 tests, coverage: 96.79%)
- bandit: PASS (0 findings)

## notes
- `MockCtx` in conftest.py gained `report_progress(progress, total, message)` and a
  `progress: list[tuple[float, float | None]]` capture list.
- Progress steps follow the linear happy-path pattern; early-exit paths naturally stop
  at whichever step they reached — this is by design (no duplicate step-3 in every
  error branch).
- `vies.py` uses 4 steps (spec requirement): prepare-request / network-call /
  parse-response / completion. Network failure exits after step 2, before parse.
- `report_progress` signature from MCP FastMCP Context:
  `async def report_progress(self, progress: float, total: float | None = None,
  message: str | None = None) -> None`
