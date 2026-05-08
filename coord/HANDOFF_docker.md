---
task_id: TASK_docker
status: DONE
timestamp: 2026-05-08T14:45:00+02:00
agent: claude-sonnet-4-6
---

## files_modified

- Dockerfile
- docker-compose.yml
- .dockerignore  (new)
- Makefile

## quality_gates

- ruff check: PASS
- ruff format: PASS
- mypy: PASS
- pytest: 62/62, coverage 94.76%
- bandit: PASS

## dockerfile_design

### Stage 1 — builder (python:3.11-slim)
- Installs gcc + libxml2-dev + libxslt1-dev for lxml C-extension builds
  (fallback for architectures without a prebuilt manylinux wheel).
- Creates /venv and runs `pip install --no-cache-dir .`
  (production deps only, no dev extras).

### Stage 2 — runtime (python:3.11-slim)
- Copies only /venv from builder — no build tools, no dev deps.
- Non-root user: `fatturapa` (uid via `useradd -r`); /app owned by that user.
- No EXPOSE — MCP runs on stdio transport, not TCP.
- PYTHONUNBUFFERED=1, PYTHONDONTWRITEBYTECODE=1 set for clean container logging.
- CMD: `fatturapa-mcp-server`

## docker_compose_services

### fatturapa-mcp (runtime target)
- Mounts `./src/fatturapa_mcp/schemas` → container schemas path (read-only).
  Comment out the volume entry to use the stub schemas bundled in the image.
- stdin_open + tty: true for MCP stdio transport.
- restart: "no" — MCP clients manage the process lifecycle.

### test (builder target)
- Installs dev extras on top of the builder venv, then runs pytest.
- Mounts src/ and tests/ read-only for iterative development without rebuilds.

## makefile_targets

```
make docker-build   →  docker build --target runtime -t fatturapa-mcp-server:latest .
make docker-run     →  docker run --rm -i fatturapa-mcp-server:latest
```

## dockerignore

Excludes: .git, __pycache__, .venv, test artefacts, .mypy_cache, .ruff_cache,
coord/, AGENTS.md, SPEC.md, CHANGELOG.md, Dockerfile itself.

## notes

- The `test` service installs dev extras at runtime (`pip install .[dev]`)
  rather than building a separate test image, keeping the Dockerfile to two
  stages and avoiding image bloat in the CI registry.
- XSD schemas are volume-mounted from the host; the stub files baked into the
  image allow `validate_invoice` to return a clear "XSD not found" error
  rather than an import failure when no real schemas are provided.
