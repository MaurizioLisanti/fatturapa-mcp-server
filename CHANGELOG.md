# Changelog

All notable changes to fatturapa-mcp-server are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [0.2.0] — 2026-05-21

### Added
- `find_invoice_anomalies` — detects anomalies in a FatturaPA XML document:
  inconsistent totals, wrong VAT, future dates, invalid P.IVA, missing recipient,
  incomplete line items, negative amounts, missing payment information
- `generate_invoice_report` — aggregates multiple FatturaPA XML documents into a
  single report with statistics, supplier/customer breakdown and anomaly summary
- Structured logging with `correlation_id` on every log entry
- Context propagation across tool calls
- Progress reporting for long-running operations
- Roots-based secure file access control

### Changed
- Total tools: 5 → 7
- Test count: increased to 162
- Coverage: improved to 95.5%
- README updated with Wave 3 and Wave 4 changelog, bilingual (IT/EN)

---

## [0.1.0] — initial release

### Added
- `validate_invoice` — validates FatturaPA XML against official AdE XSD schemas
  (v1.2 & v1.3) with automatic namespace-based version detection
- `extract_invoice_data` — extracts supplier, customer, amounts, line items and
  metadata from a valid FatturaPA document
- `lookup_sdi_error` — offline lookup of official Italian SDI error codes with
  description, category and resolution hint
- `check_piva` — validates Italian P.IVA using the official MEF checksum algorithm,
  no network call required
- `verify_piva_vies` — verifies any EU VAT number against the live VIES REST API
  with graceful degradation when the service is unavailable
- Published on PyPI — installable with `pip install fatturapa-mcp-server` or `uvx`
- CI/CD pipeline with lint, typecheck, tests, security audit (bandit + pip-audit)
- Strict mypy typing throughout
- Bilingual documentation (IT/EN)
