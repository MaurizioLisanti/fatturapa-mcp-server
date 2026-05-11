# fatturapa-mcp-server

[![CI](https://github.com/MaurizioLisanti/fatturapa-mcp-server/actions/workflows/ci.yml/badge.svg)](https://github.com/MaurizioLisanti/fatturapa-mcp-server/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-95%25-brightgreen)](https://github.com/MaurizioLisanti/fatturapa-mcp-server/actions)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## English
## The problem
Every project integrating FatturaPA
reimplements the same validation,
parsing and SDI error handling from scratch.
The result: weeks of repeated work,
hidden bugs and no standardization.

## The solution
Five production-grade AI tools installable
in one line — official AdE XSD validation,
full document parsing, offline SDI error lookup,
Italian and EU VAT verification via VIES.
## Who is it for
Python developers and AI teams working
on Italian electronic invoicing systems
who want to integrate Claude without
reimplementing FatturaPA compliance
from scratch on every project.
### What is this?

An [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) server that gives
AI assistants five ready-to-use tools for working with Italian electronic invoices
(FatturaPA) and the SDI (Sistema di Interscambio) system — no plumbing required.

### Tools

| Tool | Input | What it does |
|------|-------|--------------|
| `validate_invoice` | `xml_content` | Validates FatturaPA XML against official AdE XSD schemas (v1.2 & v1.3); auto-detects version from namespace |
| `extract_invoice_data` | `xml_content` | Extracts supplier, customer, amounts, line items and metadata from a valid FatturaPA document |
| `lookup_sdi_error` | `error_code` | Returns the official Italian description, category and resolution hint for any SDI error code (offline) |
| `check_piva` | `piva` | Validates an Italian P.IVA (VAT number) using the official MEF checksum algorithm — no network call |
| `verify_piva_vies` | `country_code`, `vat_number` | Verifies any EU VAT number against the live VIES REST API; degrades gracefully when the service is down |

### Quick start

**Option A — uvx (no install required)**

```bash
uvx fatturapa-mcp-server
```

**Option B — pip**

```bash
pip install fatturapa-mcp-server
fatturapa-mcp-server
```

### Claude Desktop configuration

Add the following block to your Claude Desktop config file:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "fatturapa": {
      "command": "uvx",
      "args": ["fatturapa-mcp-server"]
    }
  }
}
```

After restarting Claude Desktop you will see five new tools in the tool panel.

> **Note on XSD schemas:** `validate_invoice` requires the official AdE XSD files.
> See [`src/fatturapa_mcp/schemas/README.md`](src/fatturapa_mcp/schemas/README.md)
> for download instructions.

## What it demonstrates
- Production-grade MCP server with strict mypy typing
- Automated security audit — bandit + pip-audit
- Guaranteed 80% minimum coverage
- Published on PyPI — installable anywhere in one line
- Bilingual IT/EN — built for Italian and international market
## Production status
Used on real Italian electronic invoicing systems.
Tested with real SDI documents in production environments.
Part of a broader ecosystem:
domain-agent-starter → fatturapa-mcp-server → invoice-aws-ops
### Development setup

```bash
git clone https://github.com/MaurizioLisanti/fatturapa-mcp-server
cd fatturapa-mcp-server

# Install the package and all dev dependencies
make install        # pip install -e ".[dev]"

# Run the full quality gate (lint + typecheck + tests + security)
make check
```

Individual targets:

```bash
make test           # pytest with coverage (fail-under 80 %)
make lint           # ruff check + ruff format --check
make typecheck      # mypy --strict
make security       # bandit -ll + pip-audit
make format         # auto-fix formatting and imports
```

### MCP Inspector

[MCP Inspector](https://github.com/modelcontextprotocol/inspector) lets you call
tools interactively from a local web UI — useful during development:

```bash
npx @modelcontextprotocol/inspector uvx fatturapa-mcp-server
# Open http://localhost:5173 in your browser
```

### Related projects

- **[sdi-ops-monitor](https://github.com/MaurizioLisanti/sdi-ops-monitor)** — AWS-based
  pipeline that receives, stores and routes FatturaPA files from/to SDI.
  Use together with this MCP server to give Claude end-to-end visibility into
  your Italian e-invoicing operations.

---

## Italiano
## Il problema
Ogni progetto che integra FatturaPA
reimplementa da zero la stessa logica
di validazione, parsing e gestione errori SDI.
Il risultato: settimane di lavoro ripetuto,
bug nascosti e nessuna standardizzazione.
## La soluzione
Cinque tool AI production-grade installabili
in una riga — validazione XSD ufficiale AdE,
parsing completo, lookup errori SDI offline,
verifica P.IVA italiana ed europea via VIES.
## Per chi è
Developer Python e team AI che lavorano
su sistemi di fatturazione elettronica italiana
e vogliono integrare Claude senza reimplementare
la compliance FatturaPA da zero ad ogni progetto.
### Cos'è questo progetto?

Un server [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) che
fornisce agli assistenti AI cinque strumenti pronti all'uso per lavorare con le
fatture elettroniche italiane (FatturaPA) e il Sistema di Interscambio (SDI).

### Strumenti disponibili

| Strumento | Input | Cosa fa |
|-----------|-------|---------|
| `validate_invoice` | `xml_content` | Valida un XML FatturaPA contro gli XSD ufficiali AdE (v1.2 e v1.3); rileva automaticamente la versione dal namespace |
| `extract_invoice_data` | `xml_content` | Estrae fornitore, cliente, importi, righe dettaglio e metadati da un documento FatturaPA valido |
| `lookup_sdi_error` | `error_code` | Restituisce la descrizione ufficiale italiana, la categoria e il suggerimento di risoluzione per qualsiasi codice errore SDI (offline) |
| `check_piva` | `piva` | Valida una P.IVA italiana tramite l'algoritmo di checksum ufficiale MEF — nessuna chiamata di rete |
| `verify_piva_vies` | `country_code`, `vat_number` | Verifica qualsiasi partita IVA UE contro l'API REST VIES in tempo reale; risponde in modo degradato se il servizio è irraggiungibile |

### Avvio rapido

**Opzione A — uvx (nessuna installazione necessaria)**

```bash
uvx fatturapa-mcp-server
```

**Opzione B — pip**

```bash
pip install fatturapa-mcp-server
fatturapa-mcp-server
```

### Configurazione Claude Desktop

Aggiungere il seguente blocco al file di configurazione di Claude Desktop:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "fatturapa": {
      "command": "uvx",
      "args": ["fatturapa-mcp-server"]
    }
  }
}
```

Dopo il riavvio di Claude Desktop, i cinque strumenti compariranno nel pannello degli strumenti.

> **Nota sugli XSD:** `validate_invoice` richiede i file XSD ufficiali di AdE.
> Vedere [`src/fatturapa_mcp/schemas/README.md`](src/fatturapa_mcp/schemas/README.md)
> per le istruzioni di download.
## Cosa dimostra tecnicamente
- MCP server production-grade con strict typing mypy
- Security audit automatico — bandit + pip-audit
- Coverage minima garantita all'80%
- Pubblicato su PyPI — installabile ovunque con una riga
- Bilingue IT/EN — pensato per mercato italiano e internazionale
  ## In produzione
Usato su sistemi reali di fatturazione elettronica italiana.
Testato con documenti SDI reali in ambiente di produzione.
Parte di un ecosistema più ampio:
domain-agent-starter → fatturapa-mcp-server → sdi-ops-monitor

### Setup per lo sviluppo

```bash
git clone https://github.com/MaurizioLisanti/fatturapa-mcp-server
cd fatturapa-mcp-server

# Installa il pacchetto e tutte le dipendenze di sviluppo
make install        # pip install -e ".[dev]"

# Esegui il quality gate completo (lint + typecheck + test + security)
make check
```

Target individuali:

```bash
make test           # pytest con coverage (fail-under 80 %)
make lint           # ruff check + ruff format --check
make typecheck      # mypy --strict
make security       # bandit -ll + pip-audit
make format         # correzione automatica formattazione e import
```

### MCP Inspector

[MCP Inspector](https://github.com/modelcontextprotocol/inspector) permette di
invocare gli strumenti in modo interattivo da una web UI locale — utile durante lo sviluppo:

```bash
npx @modelcontextprotocol/inspector uvx fatturapa-mcp-server
# Aprire http://localhost:5173 nel browser
```

### Progetti correlati

- **[sdi-ops-monitor](https://github.com/MaurizioLisanti/sdi-ops-monitor)** — Pipeline AWS
  per ricevere, archiviare e instradare i file FatturaPA da/verso il SDI.
  Da usare insieme a questo server MCP per dare a Claude visibilità end-to-end
  sulle operazioni di fatturazione elettronica italiana.

---

## License / Licenza

[MIT](LICENSE)
