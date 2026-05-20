---
task_id: TASK_find_invoice_anomalies
status: DONE
timestamp: 2026-05-20T17:35:00+02:00
agent: claude-sonnet-4-6
---

## files_modified
- src/fatturapa_mcp/tools/anomalies.py (created)
- src/fatturapa_mcp/server.py (registered tool)
- tests/test_anomalies.py (created)
- coord/STATE.json (updated)

## tests_added
- tests/test_anomalies.py::TestFindInvoiceAnomaliesClean::test_clean_invoice_is_clean
- tests/test_anomalies.py::TestFindInvoiceAnomaliesClean::test_result_has_all_required_keys
- tests/test_anomalies.py::TestFindInvoiceAnomaliesDetection::test_total_mismatch
- tests/test_anomalies.py::TestFindInvoiceAnomaliesDetection::test_vat_mismatch
- tests/test_anomalies.py::TestFindInvoiceAnomaliesDetection::test_future_date
- tests/test_anomalies.py::TestFindInvoiceAnomaliesDetection::test_invalid_piva_supplier
- tests/test_anomalies.py::TestFindInvoiceAnomaliesDetection::test_invalid_piva_customer
- tests/test_anomalies.py::TestFindInvoiceAnomaliesDetection::test_missing_dest_code
- tests/test_anomalies.py::TestFindInvoiceAnomaliesDetection::test_suspicious_dest_code
- tests/test_anomalies.py::TestFindInvoiceAnomaliesDetection::test_incomplete_line_missing_description
- tests/test_anomalies.py::TestFindInvoiceAnomaliesDetection::test_incomplete_line_missing_price
- tests/test_anomalies.py::TestFindInvoiceAnomaliesDetection::test_negative_amount_not_td04
- tests/test_anomalies.py::TestFindInvoiceAnomaliesDetection::test_negative_amount_td04_allowed
- tests/test_anomalies.py::TestFindInvoiceAnomaliesDetection::test_missing_payment
- tests/test_anomalies.py::TestFindInvoiceAnomaliesDetection::test_errors_and_warnings_are_partitioned
- tests/test_anomalies.py::TestFindInvoiceAnomaliesCtx::test_progress_emits_four_steps
- tests/test_anomalies.py::TestFindInvoiceAnomaliesCtx::test_ctx_emits_start_and_done
- tests/test_anomalies.py::TestFindInvoiceAnomaliesCtx::test_no_ctx_does_not_raise
- tests/test_anomalies.py::TestFindInvoiceAnomaliesFilePath::test_file_path_within_roots
- tests/test_anomalies.py::TestFindInvoiceAnomaliesFilePath::test_file_path_outside_roots_raises
- tests/test_anomalies.py::TestFindInvoiceAnomaliesFilePath::test_neither_xml_nor_file_path_raises

## quality_gates
- ruff: PASS
- mypy: PASS (strict, 0 errors, 12 source files)
- pytest: PASS (142 passed, coverage 94.80% total, 91% on anomalies.py)
- bandit: PASS (0 findings)

## notes
- P.IVA validation delegates to the existing `check_piva()` tool with `ctx=None`
  to avoid spurious log entries; only Italian PIVAs (IdPaese=="IT") are checked.
- The `_TOLERANCE = 0.02` constant absorbs legitimate rounding differences in
  monetary sums; amounts are compared against declared totals, not re-derived.
- Negative-amount check (NEGATIVE_AMOUNT) fires only when TipoDocumento != "TD04"
  (nota di credito); TD04 documents are expected to carry negative totals.
- The clean-invoice test uses checksummed-valid PIVAs (12345678903, 98765432103)
  rather than the fixture values in valid_v13.xml which would fail checksum.
- 4 progress steps: (1) parse, (2) document checks, (3) line checks, (4) party checks.
