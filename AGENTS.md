# AGENTS.md — fatturapa-mcp-server

Rules and contracts for AI agents working on this repository.
Read this file completely before starting any task.

---

## Stack

Python 3.11 · mcp[cli] · lxml · httpx · pytest · ruff · mypy strict

---

## Quality Gates (all blocking — zero exceptions)

| Gate | Command | Required result |
|------|---------|----------------|
| Lint | `ruff check src/ tests/` | PASS (0 errors) |
| Format | `ruff format --check src/ tests/` | PASS |
| Type check | `mypy src/` | PASS (strict, 0 errors) |
| Tests | `pytest --cov-fail-under=80` | PASS (coverage ≥ 80%) |
| Security | `bandit -r src/ -ll` | 0 MEDIUM or HIGH findings |
| Dependencies | `pip-audit` | 0 known vulnerabilities |

Run all gates with: `make check`

---

## Code Standards

- All code, comments, and docstrings in **English**
- Inline comments explain the WHY, never the WHAT
- Docstring required on every public function, method, and class
- Naming: `PascalCase` for classes, `snake_case` for functions/variables,
  `UPPER_SNAKE_CASE` for module-level constants
- No function body longer than 30 lines (excluding docstring)
- Complete type hints on every signature — `mypy --strict` must pass
- **Never log XML content** — only derived metadata (invoice number, P.IVA, etc.)
- Every log entry must include a `correlation_id` field
- No `Any` type unless absolutely unavoidable and documented with a comment

---

## Smoke Test Protocol (post-merge)

```
make test
```

- **PASS** → update `coord/STATE.json` task status to `DONE`, move to next task
- **FAIL** → task status → `NEEDS_REVIEW`, do not proceed

---

## MCP Tools — Implementation Order

| # | Tool | Command | Dependency |
|---|------|---------|-----------|
| 1 | `validate_invoice` | `TASK_validate_invoice` | — |
| 2 | `extract_invoice_data` | `TASK_extract_invoice_data` | #1 |
| 3 | `lookup_sdi_error` | `TASK_lookup_sdi_error` | — |
| 4 | `check_piva` | `TASK_check_piva` | — |
| 5 | `verify_piva_vies` | `TASK_verify_piva_vies` | #4 |

---

## Non-Goals

The following are explicitly out of scope — do not implement:

- No database or persistent storage of any kind
- No digital signature creation or verification of invoices
- No direct communication with the SDI (Sistema di Interscambio)
- No persistence of XML content beyond the duration of a single tool call
- No authentication layer on the MCP server

---

## Handoff Schema

After completing each task, produce `coord/HANDOFF_<taskname>.md`:

```markdown
---
task_id: TASK_<name>
status: DONE | FAILED | NEEDS_REVIEW
timestamp: <ISO8601>
agent: <agent identifier>
---

## files_modified
- path/to/file.py

## tests_added
- tests/test_foo.py::TestClass::test_method

## quality_gates
- ruff: PASS
- mypy: PASS
- pytest: PASS (coverage: XX%)
- bandit: PASS (0 findings)
- pip-audit: PASS

## notes
Any non-obvious decisions or caveats.
```

Then update `coord/STATE.json` with the new task status and timestamp.
