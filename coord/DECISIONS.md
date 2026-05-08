# Architectural Decisions — fatturapa-mcp-server

## ADR-001: src layout for Python package

**Decision**: Use `src/fatturapa_mcp/` layout instead of flat layout.

**Rationale**: Prevents accidental imports of the uninstalled package during
testing; enforces that the installed package is always what is tested.

**Date**: 2026-05-08

---

## ADR-002: lxml for XML parsing and XSD validation

**Decision**: Use `lxml` (libxml2 binding) for both parsing and XSD validation.

**Rationale**: `lxml` is the only Python XML library with native XSD 1.0
validation support via `etree.XMLSchema`. The standard `xml.etree.ElementTree`
does not support XSD validation at all.

**Date**: 2026-05-08

---

## ADR-003: No XML data in logs

**Decision**: Log only derived metadata (e.g., invoice number, P.IVA, schema
version). Never log raw XML strings or node values.

**Rationale**: FatturaPA documents can contain PII (names, addresses, fiscal
codes). Keeping XML out of logs avoids accidental GDPR exposure via log
aggregation pipelines.

**Date**: 2026-05-08

---

## ADR-004: VIES fallback instead of hard failure

**Decision**: `verify_piva_vies` returns `source="unavailable"` on timeout
or HTTP error, rather than raising an exception.

**Rationale**: VIES has documented availability issues. Failing hard would
break invoice processing workflows. The caller must check the `source` field
and decide whether to treat unavailability as valid or invalid.

**Date**: 2026-05-08

---

## ADR-005: XSD files not bundled — downloaded by operator

**Decision**: XSD files are not committed to the repository.

**Rationale**: AdE updates schemas independently of software releases.
Bundling XSDs would require a code release for every schema revision.
The `schemas/README.md` documents exactly where to obtain the files.

**Date**: 2026-05-08

---

## ADR-006: optional-dependencies instead of dependency-groups

**Decision**: Use `[project.optional-dependencies]` for dev deps, not PEP 735
`[dependency-groups]`.

**Rationale**: `pip install -e ".[dev]"` (used in Makefile and CI) requires
`[project.optional-dependencies]`. PEP 735 `dependency-groups` are only
supported by `uv` and very recent pip versions. Using the older mechanism
maximises toolchain compatibility.

**Date**: 2026-05-08
