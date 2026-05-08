---
task_id: TASK_readme_bilingual
status: DONE
timestamp: 2026-05-08T14:30:00+02:00
agent: claude-sonnet-4-6
---

## files_modified

- README.md
- CHANGELOG.md

## quality_gates

- ruff check: PASS
- ruff format: PASS
- mypy: PASS
- pytest: 62/62, coverage 94.76%
- bandit: PASS

## readme_structure

### English section
- Badges: CI (GitHub Actions), Coverage (95 %), Python 3.11+, License MIT
- One-liner description
- Tools table: 5 tools with Input + What it does columns
- Quick start: uvx (Option A) + pip (Option B)
- Claude Desktop config JSON (macOS + Windows paths)
- Note on XSD schemas with link to schemas/README.md
- Development setup: git clone → make install → make check
- Individual make targets documented
- MCP Inspector: npx invocation + URL
- Related projects: invoice-aws-ops (complementary AWS pipeline)

### Italian section
- Mirrors English section with full Italian translations
- Same structure, same completeness

## changelog_updates

- [Unreleased] section expanded with Wave 1 and Wave 2 entries
- Each Wave 1 tool entry describes implementation choices and key behaviors
- Wave 2 CI entry summarises pipeline steps and triggers
- Keep a Changelog format maintained
- compare link placeholder: your-org/fatturapa-mcp-server

## notes

- GitHub URLs use `your-org` placeholder — replace with actual org before publishing.
- Coverage badge shows static 95 % — replace with Codecov badge once repo is public
  and Codecov is configured with the coverage.xml artifact from CI.
