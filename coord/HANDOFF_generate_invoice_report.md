---
task_id: TASK_generate_invoice_report
status: DONE
timestamp: 2026-05-20T17:47:00+02:00
agent: claude-sonnet-4-6
---

## files_modified
- src/fatturapa_mcp/tools/report.py (created)
- src/fatturapa_mcp/server.py (registered tool)
- tests/test_report.py (created)
- coord/STATE.json (updated — wave_4 status: DONE)

## tests_added
- tests/test_report.py::TestGenerateInvoiceReportStructure::test_result_has_all_required_keys
- tests/test_report.py::TestGenerateInvoiceReportStructure::test_default_title
- tests/test_report.py::TestGenerateInvoiceReportStructure::test_custom_title
- tests/test_report.py::TestGenerateInvoiceReportStructure::test_generated_at_is_iso8601
- tests/test_report.py::TestGenerateInvoiceReportStructure::test_currency_from_invoice
- tests/test_report.py::TestGenerateInvoiceReportCounts::test_empty_list
- tests/test_report.py::TestGenerateInvoiceReportCounts::test_single_invoice_totals
- tests/test_report.py::TestGenerateInvoiceReportCounts::test_multiple_invoices_sums
- tests/test_report.py::TestGenerateInvoiceReportCounts::test_invalid_invoice_counted
- tests/test_report.py::TestGenerateInvoiceReportCounts::test_all_invalid_invoices
- tests/test_report.py::TestGenerateInvoiceReportParties::test_supplier_appears_in_output
- tests/test_report.py::TestGenerateInvoiceReportParties::test_same_supplier_aggregated
- tests/test_report.py::TestGenerateInvoiceReportAnomalies::test_clean_invoice_anomaly_summary
- tests/test_report.py::TestGenerateInvoiceReportAnomalies::test_anomaly_detected_and_counted
- tests/test_report.py::TestGenerateInvoiceReportAnomalies::test_by_code_aggregates_across_invoices
- tests/test_report.py::TestGenerateInvoiceReportCtx::test_progress_empty_list
- tests/test_report.py::TestGenerateInvoiceReportCtx::test_progress_one_invoice
- tests/test_report.py::TestGenerateInvoiceReportCtx::test_progress_two_invoices
- tests/test_report.py::TestGenerateInvoiceReportCtx::test_ctx_emits_start_and_done
- tests/test_report.py::TestGenerateInvoiceReportCtx::test_no_ctx_does_not_raise

## quality_gates
- ruff: PASS
- mypy: PASS (strict, 0 errors, 13 source files)
- pytest: PASS (162 passed, coverage 95.50% total, 99% on report.py)
- bandit: PASS (0 findings)

## notes
- `extract_invoice_data()` and `find_invoice_anomalies()` are called with
  `ctx=None` for sub-invocations to avoid spurious log/progress noise from
  the report tool's own progress stream.
- Broad `except Exception` catch in the per-invoice loop is intentional:
  a single unparseable invoice must not abort the entire batch report.
- `total_vat` is derived from line items (total_price * vat_rate / 100),
  not from DatiRiepilogo, to stay within the existing extract_invoice_data API.
- `supplier_piva` / `customer_piva` carry the IdPaese prefix (e.g. "IT12345678903")
  as returned by extract_invoice_data — this is consistent with the existing
  extract tool contract.
- wave_4.status set to DONE: both TASK_find_invoice_anomalies and
  TASK_generate_invoice_report completed.
