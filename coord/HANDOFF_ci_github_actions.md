---
task_id: TASK_ci_github_actions
status: DONE
timestamp: 2026-05-08T14:20:00+02:00
agent: claude-sonnet-4-6
---

## files_modified

- .github/workflows/ci.yml

## quality_gates

- ruff check: PASS
- ruff format: PASS
- mypy: PASS
- pytest: 62/62, coverage 94.76%
- bandit: PASS

## pipeline_steps (in order)

1. actions/checkout@v4 (fetch-depth: 0 for gitleaks full history scan)
2. actions/setup-python@v5 with pip cache (Python 3.11)
3. pip install -e ".[dev]"
4. ruff check src/ tests/
5. ruff format --check src/ tests/
6. mypy src/
7. pytest -q --cov-report=xml  (--cov-fail-under=80 from pyproject.toml addopts)
8. actions/upload-artifact@v4 — coverage.xml (always, for inspection on failure)
9. bandit -r src/ -ll
10. pip-audit
11. gitleaks/gitleaks-action@v2 (GITHUB_TOKEN env)

## triggers

- push: branches [main, develop]
- pull_request: branches [main]

## notes

- `cache: "pip"` in setup-python speeds up installs by caching the pip download cache.
- `fetch-depth: 0` is required by gitleaks to scan full git history for secrets.
- Coverage XML artifact uploaded unconditionally (`if: always()`) so failures
  can be diagnosed even when the test step itself fails.
- `--cov-fail-under=80` is enforced via pytest addopts in pyproject.toml,
  not duplicated in the CI command, to keep the single source of truth.
