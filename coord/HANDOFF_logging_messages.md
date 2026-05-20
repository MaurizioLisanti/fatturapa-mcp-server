---
task_id: TASK_logging_messages
status: DONE
timestamp: 2026-05-20T08:15:00+02:00
agent: Claude Code (claude-sonnet-4-6)
---

## files_modified
- src/fatturapa_mcp/utils/logging.py
- src/fatturapa_mcp/tools/validate.py
- src/fatturapa_mcp/tools/extract.py
- src/fatturapa_mcp/tools/sdi_errors.py
- src/fatturapa_mcp/tools/check_piva.py
- src/fatturapa_mcp/tools/vies.py
- tests/conftest.py
- tests/test_logging.py
- tests/test_validate.py
- tests/test_extract.py
- tests/test_sdi_errors.py
- tests/test_check_piva.py
- tests/test_vies.py

## tests_added
- tests/test_logging.py::TestGetLogger::* (5 new tests — real get_logger implementation)
- tests/test_logging.py::TestBuildLogMsg::* (2 new tests)
- tests/test_logging.py::TestElapsedMs::* (2 new tests)
- tests/test_logging.py::TestCtxLog::* (5 new tests)
- tests/test_validate.py::TestValidateInvoiceCtxLogging::* (4 new tests)
- tests/test_extract.py::TestExtractInvoiceDataCtxLogging::* (1 new test)
- tests/test_sdi_errors.py::TestLookupSdiErrorCtxLogging::* (2 new tests)
- tests/test_check_piva.py::TestCheckPivaCtxLogging::* (2 new tests)
- tests/test_vies.py::TestVerifyPivaViesCtxLogging::* (2 new tests)

## quality_gates
- ruff: PASS (0 errors)
- ruff format: PASS
- mypy: PASS (strict, 0 errors)
- pytest: PASS (86/86, coverage: 96.43%)
- bandit: PASS (0 findings)

## notes

### Tools made async
All five tools are now `async def`. This was required to `await ctx_log(...)` calls.
Sync callers that used `validate_invoice(xml)` without `await` must be updated — all
62 existing test methods were migrated to `async def` with `await`.
`asyncio_mode = "auto"` in pyproject.toml makes this transparent to pytest.

### Shared logging helpers in utils/logging.py
Three new public functions added:
- `build_log_msg(event, **kw)` — serialises an event + metadata as a JSON string
- `elapsed_ms(start)` — computes duration from a `time.monotonic()` reference
- `ctx_log(ctx, event, level, **kw)` — no-op when ctx is None; routes to
  `ctx.info / ctx.warning / ctx.error` based on `level` string

`ctx: Any` is intentional and documented: FastMCP's `Context` type parameters are
opaque to tool implementations (same rationale as the pre-existing `_Ctx` alias).

### Privacy rules enforced
- No XML content in any log entry
- P.IVA is never logged; only `input_length` / `valid` / `reason` metadata
- Log payloads: lengths, counts, boolean outcomes, elapsed_ms, error codes

### MockCtx fixture
`tests/conftest.py` now exports `MockCtx` and a `mock_ctx` fixture. Each ctx
logging test uses `# type: ignore[arg-type]` on the ctx argument — `MockCtx`
satisfies the structural interface but is not assignable to `Context[Any,Any,Any]`
at the static type level.

### get_logger implementation
`_JsonFormatter` serialises `levelname`, `logger.name`, and `getMessage()` into a
JSON object, then merges any extra fields not present in `_STDLIB_LOG_ATTRS`.
`get_logger` idempotently attaches one handler (avoids duplicate handlers across
repeated calls within the same process).
