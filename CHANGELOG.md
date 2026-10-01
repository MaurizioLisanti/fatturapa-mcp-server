# Changelog

All notable changes to fatturapa-mcp-server are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [0.3.2] — 2026-10-01

### Fixed
- **The server did not start on Python 3.11**, although the package declares
  `requires-python >=3.11`. FastMCP builds tool schemas with Pydantic, which
  rejects nested `typing.TypedDict` below Python 3.12. `TypedDict` now comes from
  `typing_extensions`. CI ran on 3.11 and stayed green because `server.py` was
  excluded from coverage and never imported by any test.
- The MCP handshake declared the version of the `mcp` library (1.30.0) instead
  of the package version.

### Added
- Startup tests: tool registration, no `ctx` in tool schemas, and a real stdio
  handshake. Verified to fail with the bug reintroduced.
- CI matrix on Python 3.11, 3.12 and 3.13.
- `server.json` and `mcp-name` for the official MCP Registry.

### Documentation
- README: removed claims that were not true. `validate_invoice` does not yet
  validate against the official AdE XSD (the bundled schemas are structural
  stubs), and the project is not used in production. Added a **Known
  limitations** section from an audit with synthetic invoices checked against
  the official FatturaPA v1.2.3 schema.
- Documented `FATTURAPA_ALLOWED_ROOTS` in the Claude Desktop configuration.

---

## [0.3.1] — 2026-08-01

### Fixed
- **Pin `mcp` below 2.0.0.** The dependency was declared as `mcp[cli]>=1.0.0`
  with no upper bound. The 2.0 line removed `mcp.server.fastmcp`, which every
  tool module imports, so from the day 2.0.0 shipped a fresh
  `pip install fatturapa-mcp-server` resolved to a release this package cannot
  import at all — including 0.3.0, already published. Nothing in this package
  changed; the constraint was simply wrong.

### Notes
Lifting the bound means migrating to the 2.x API, not relaxing the constraint.
Runtime dependencies now carry upper bounds where a major release is known to
be incompatible; dev tool versions were already pinned exactly.

---

## [0.3.0] — 2026-07-21

### Security
- **BREAKING** — file-system access now fails closed. Previously, when
  `FATTURAPA_ALLOWED_ROOTS` was unset the guard permitted every path, so a
  default deployment could read any file the process could reach. Since this
  server is driven by an LLM agent processing untrusted documents, that default
  turned a prompt injection into arbitrary file disclosure.
- Tools that take a `file_path` argument now refuse the read unless
  `FATTURAPA_ALLOWED_ROOTS` names a directory containing it.
- Added `FATTURAPA_ALLOW_ALL_PATHS` as an explicit, documented opt-out for the
  previous behaviour. It logs a warning once per process when active.

### Added
- `ensure_path_allowed()` — raising wrapper that distinguishes the two denial
  causes, so the message tells the operator what to fix.
- `is_unrestricted_mode()` — reports whether the guard has been opted out of.

### Changed
- The `list_allowed_roots` resource now reports three states instead of two:
  configured roots, `(unrestricted)`, or `(no roots configured)`.

### Migration
Deployments that read invoices from disk must now declare where:

```bash
export FATTURAPA_ALLOWED_ROOTS=/srv/invoices:/mnt/incoming
```

Deployments that pass documents via `xml_content` are unaffected.
Setting `FATTURAPA_ALLOW_ALL_PATHS=1` restores the 0.2.0 behaviour, but is
not recommended outside a sandbox.

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
