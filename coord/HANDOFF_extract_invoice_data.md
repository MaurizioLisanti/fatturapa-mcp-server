---
task_id: TASK_extract_invoice_data
status: DONE
timestamp: 2026-05-08T12:20:00+02:00
agent: claude-sonnet-4-6
---

## files_modified

- src/fatturapa_mcp/tools/extract.py
- src/fatturapa_mcp/server.py
- tests/test_extract.py

## tests_added

- tests/test_extract.py::TestExtractInvoiceData::test_extracts_supplier_name_v13
- tests/test_extract.py::TestExtractInvoiceData::test_extracts_supplier_piva_v13
- tests/test_extract.py::TestExtractInvoiceData::test_supplier_tax_code_absent_returns_none
- tests/test_extract.py::TestExtractInvoiceData::test_extracts_customer_name_v13
- tests/test_extract.py::TestExtractInvoiceData::test_extracts_customer_piva_v13
- tests/test_extract.py::TestExtractInvoiceData::test_extracts_invoice_number_and_date_v13
- tests/test_extract.py::TestExtractInvoiceData::test_extracts_document_type_and_currency_v13
- tests/test_extract.py::TestExtractInvoiceData::test_extracts_total_amount_v13
- tests/test_extract.py::TestExtractInvoiceData::test_extracts_one_line_item_v13
- tests/test_extract.py::TestExtractInvoiceData::test_line_item_fields_v13
- tests/test_extract.py::TestExtractInvoiceData::test_extracts_basic_fields_from_v12
- tests/test_extract.py::TestExtractInvoiceData::test_minimal_xml_all_fields_none
- tests/test_extract.py::TestExtractInvoiceData::test_nome_cognome_fallback
- tests/test_extract.py::TestExtractInvoiceData::test_total_from_dati_riepilogo_fallback
- tests/test_extract.py::TestExtractInvoiceData::test_malformed_xml_raises

## quality_gates

- ruff check: PASS (0 errors)
- ruff format: PASS (all files formatted)
- mypy: PASS (strict, 10 source files, 0 errors)
- pytest: PASS (31/31, coverage: extract.py 89%, overall 92%)
- bandit: PASS (0 MEDIUM/HIGH findings)
- pip-audit: not run (network-dependent; run manually before release)

## make check output

```
All checks passed!
18 files already formatted
Success: no issues found in 10 source files
...............................                                          [100%]
Total coverage: 92.42%
31 passed in 0.38s
No issues identified.
All checks passed.
```

## notes

- `_SAFE_PARSER` imported from `validate.py` — no duplication of XXE-safe parser settings.
- `supplier_piva` / `customer_piva` are formatted as `{IdPaese}{IdCodice}` (e.g. `"IT12345678901"`).
- `supplier_tax_code` / `customer_tax_code` map to `CodiceFiscale`; absent in both fixtures → None.
- `total_amount` uses `ImportoTotaleDocumento` as primary source; falls back to summing
  `DatiBeniServizi/DatiRiepilogo/(ImponibileImporto + Imposta)` across the first body.
- `supplier_name` falls back to `Nome + " " + Cognome` when `Denominazione` is absent;
  covered by the `_XML_NOME_COGNOME` inline fixture in the test module.
- Both `validate_invoice` and `extract_invoice_data` are now registered in `server.py`
  via `mcp.tool()(fn)` — server.py is excluded from coverage by pyproject config.
- Uncovered lines in extract.py (53-54, 60, 63-64, 70, 86, 93, 100, 115) are all
  defensive `except ValueError` / `return None` guard paths; 89% > 80% gate.
