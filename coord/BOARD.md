# Operational Board — fatturapa-mcp-server

## Wave 1 — Core Tools

| Task | Status | Owner | Notes |
|------|--------|-------|-------|
| TASK_scaffold | DONE | AI Agent | Repo structure, pyproject, CI, fixtures |
| TASK_validate_invoice | DONE | AI Agent | XSD v1.2+v1.3 auto-detect |
| TASK_extract_invoice_data | DONE | AI Agent | XPath extraction, TypedDict, 15 tests |
| TASK_lookup_sdi_error | TODO | — | Static SDI error table |
| TASK_check_piva | TODO | — | Local checksum algorithm |
| TASK_verify_piva_vies | TODO | — | Blocked by TASK_check_piva |

## Wave 2 — Polish & DevEx

| Task | Status | Notes |
|------|--------|-------|
| TASK_ci_github_actions | TODO | Fine-tune CI gates |
| TASK_readme_bilingual | TODO | Expand EN+IT docs |
| TASK_docker | TODO | Production Dockerfile |

## Legend

- **TODO** — not started
- **IN_PROGRESS** — agent working
- **NEEDS_REVIEW** — completed, awaiting quality gate check
- **DONE** — all quality gates passed, handoff produced

## Last updated

2026-05-08T12:20:00+02:00
