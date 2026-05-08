# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

#### Wave 2

- **CI GitHub Actions** (`.github/workflows/ci.yml`): full pipeline with
  ruff → mypy → pytest (coverage fail-under 80 %) → bandit → pip-audit →
  gitleaks secret scan; triggers on push to `main`/`develop` and PRs to `main`;
  pip cache and XML coverage artifact upload.
- **README bilingue** (EN + IT): badges CI/coverage/Python/MIT, tabella 5 tool,
  quick start uvx, configurazione Claude Desktop, setup sviluppo, MCP Inspector,
  link a invoice-aws-ops.
- **Docker** (wave 2 in progress): Dockerfile multi-stage, docker-compose.yml,
  `make docker-build` / `make docker-run`.

#### Wave 1

- **`validate_invoice`**: validates FatturaPA XML (v1.2 & v1.3) against official
  AdE XSD schemas; auto-detects schema version from XML namespace; returns
  `valid`, `version`, `errors` — XXE-safe parser (`resolve_entities=False`,
  `no_network=True`).
- **`extract_invoice_data`**: extracts supplier/customer identity, invoice
  number/date, total amount, currency, document type and line items from a
  valid FatturaPA document; falls back to `Nome+Cognome` when `Denominazione`
  is absent; falls back to `DatiRiepilogo` for total when
  `ImportoTotaleDocumento` is missing.
- **`lookup_sdi_error`**: static lookup table of 30 official AdE SDI error codes
  across four categories (STRUTTURA, CONTENUTO, FIRMA, RECAPITO); raises
  `ValueError` for unknown codes.
- **`check_piva`**: Italian P.IVA validation using the official MEF checksum
  algorithm (S_odd + S_even mod 10); strips `IT` prefix and whitespace; fully
  offline.
- **`verify_piva_vies`**: async verification against the EU VIES REST API v2;
  maps `"---"` undisclosed fields to `None`; any `httpx.HTTPError`,
  `TimeoutException` or JSON parse error returns `source="unavailable"` without
  raising.
- **Project scaffold**: `src/` layout, `pyproject.toml` (ruff, mypy strict,
  bandit, pytest-cov, pytest-httpx), `Makefile`, FatturaPA XML test fixtures
  (v1.2, v1.3, invalid), XSD schema stubs, `AGENTS.md`, `SPEC.md`, `coord/`
  directory with `STATE.json`, `BOARD.md`, `DECISIONS.md`.

### Changed

- `pyproject.toml`: added `pytest-httpx>=0.30.0` to dev dependencies for
  VIES HTTP mocking.

[Unreleased]: https://github.com/your-org/fatturapa-mcp-server/compare/HEAD...HEAD
