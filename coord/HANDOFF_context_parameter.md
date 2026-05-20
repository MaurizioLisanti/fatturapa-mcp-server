---
task_id: TASK_context_parameter
status: DONE
timestamp: 2026-05-19T13:50:00+02:00
agent: Claude Code (claude-sonnet-4-6)
---

## files_modified
- src/fatturapa_mcp/tools/validate.py
- src/fatturapa_mcp/tools/extract.py
- src/fatturapa_mcp/tools/sdi_errors.py
- src/fatturapa_mcp/tools/check_piva.py
- src/fatturapa_mcp/tools/vies.py

## tests_added
[]

## quality_gates
- ruff: PASS
- mypy: PASS (strict, 0 errors)
- pytest: PASS (62/62, coverage: 95.02%)
- bandit: PASS (0 findings)
- pip-audit: not re-run (no new dependencies)

## notes
Context parameter aggiunto a tutti i 5 tool come `ctx: _Ctx | None = None`.

`Context` è un tipo generico `Context[ServerSessionT, LifespanContextT, RequestT]`
(tre TypeVar interni a FastMCP). Poiché nessun tool usa gli internals della sessione,
è stata definita un'alias locale `_Ctx = Context[Any, Any, Any]` in ogni file,
con commento esplicativo per rispettare la policy AGENTS.md ("No Any unless
absolutely unavoidable and documented").

Il parametro `ctx` è opzionale (`= None`) per garantire piena retrocompatibilità:
tutti i 62 test esistenti continuano a passare senza modifiche.

FastMCP inietta il context automaticamente al runtime tramite ispezione della firma;
non è stato necessario modificare `server.py` (nessun import di `Context` lì, per
evitare F401 ruff su import inutilizzato).
