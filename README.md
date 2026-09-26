# fatturapa-mcp-server

<!-- mcp-name: io.github.MaurizioLisanti/fatturapa-mcp-server -->

[![CI](https://github.com/MaurizioLisanti/fatturapa-mcp-server/actions/workflows/ci.yml/badge.svg)](https://github.com/MaurizioLisanti/fatturapa-mcp-server/actions/workflows/ci.yml)
[![Coverage gate](https://img.shields.io/badge/coverage%20gate-80%25%20enforced-brightgreen)](https://github.com/MaurizioLisanti/fatturapa-mcp-server/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

# English
## The problem
Every project integrating FatturaPA
reimplements the same validation,
parsing and SDI error handling from scratch.
The result: weeks of repeated work,
hidden bugs and no standardization.

## The solution
Seven AI tools installable in one line —
document parsing, anomaly detection on received
invoices, multi-invoice reporting, Italian and EU
VAT verification via VIES, structural XML checks
and offline SDI error lookup.

> **Status: beta.** See [Known limitations](#known-limitations-v032) before
> relying on validation results.
## Who is it for
Python developers and AI teams working
on Italian electronic invoicing systems
who want to integrate Claude without
reimplementing FatturaPA compliance
from scratch on every project.
### What is this?

An [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) server that gives
AI assistants seven ready-to-use tools for working with Italian electronic invoices
(FatturaPA) and the SDI (Sistema di Interscambio) system — no plumbing required.

### Tools

| Tool | Input | What it does |
|------|-------|--------------|
| `validate_invoice` | `xml_content` | Checks that the XML is well-formed and has the FatturaPA root structure. ⚠️ **Not yet a full schema validation** — see Known limitations |
| `extract_invoice_data` | `xml_content` | Extracts supplier, customer, amounts, line items and metadata from a valid FatturaPA document |
| `lookup_sdi_error` | `error_code` | Returns description, category and resolution hint for SDI error codes (offline). ⚠️ The table is being realigned with the official list — see Known limitations |
| `check_piva` | `piva` | Validates an Italian P.IVA (VAT number) using the official MEF checksum algorithm — no network call |
| `verify_piva_vies` | `country_code`, `vat_number` | Verifies any EU VAT number against the live VIES REST API; degrades gracefully when the service is down |
| `find_invoice_anomalies` | `xml_content` | Detects anomalies in a FatturaPA XML document: inconsistent totals, wrong VAT, future dates, invalid P.IVA, missing recipient, incomplete line items, negative amounts, missing payment info |
| `generate_invoice_report` | `xml_contents` | Aggregates multiple FatturaPA XML documents into a single report with statistics, supplier/customer breakdown and anomaly summary |

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
      "args": ["fatturapa-mcp-server"],
      "env": { "FATTURAPA_ALLOWED_ROOTS": "/path/to/your/invoices" }
    }
  }
}
```

`FATTURAPA_ALLOWED_ROOTS` lists the only folders the server may read (`:` separated
on macOS/Linux, `;` on Windows). Without it every `file_path` read is refused and
documents must be passed as `xml_content`. This is deliberate: the server is driven
by an AI agent reading untrusted documents.

After restarting Claude Desktop you will see seven new tools in the tool panel.

### Known limitations (v0.3.2)

An audit against the official AdE schema (FatturaPA v1.2.3) with synthetic invoices
found the following. They are being fixed in the next releases; until then:

- **`validate_invoice` is structural only.** The bundled XSD files are stubs: an
  invoice with an unknown document type (`TD99`), an invalid currency (`EURO`) or
  missing mandatory blocks is reported as `valid: true`. Do not use it as a
  substitute for SDI validation.
- **`lookup_sdi_error`**: several codes have descriptions that differ from the
  official list (e.g. `00001` is "invalid file name"), and some codes are missing.
- **Batches (lots)**: when a file contains more than one invoice, only the first
  one is fully analysed.
- **Encoding**: XML declared as ISO-8859-1 / windows-1252 may be decoded incorrectly.
- **`.p7m`** signed files are not supported yet: extract the XML first.
- **Report**: credit notes (TD04) are added instead of subtracted; totals across
  different currencies are summed.
- Amounts are returned as floats.

What *is* solid today: coherence checks (totals, VAT, P.IVA checksum, dates),
fail-closed file access, XXE protection, VIES degradation when the service is down.

## Changelog / Release history

| Wave | Tools / Features | Release |
|------|-----------------|---------|
| Wave 1 | `validate_invoice`, `extract_invoice_data`, `lookup_sdi_error`, `check_piva`, `verify_piva_vies` | v0.1.0 |
| Wave 2 | PyPI publication, CI/CD, security audit, full coverage | v0.1.0 |
| Wave 3 | Context propagation, structured logging, progress reporting, roots-based secure file access | v0.1.x |
| Wave 4 | `find_invoice_anomalies`, `generate_invoice_report` | v0.2.0 |

**v0.3.2 stats:** 7 tools · 181 tests · 95% coverage, including server startup

## What it demonstrates
- MCP server with strict mypy typing, tested on Python 3.11, 3.12 and 3.13
- Automated security audit — bandit + pip-audit
- Guaranteed 80% minimum coverage (currently 95% across 181 tests)
- Fail-closed file-system access: reads are refused unless explicitly configured
- Published on PyPI — installable anywhere in one line
- Bilingual IT/EN — built for Italian and international market

### Auditable by design

Every feature in this repository was built through a governed multi-agent
pipeline — planner, executor and reviewer as separate roles, each with declared
authority and hard quality gates between them.

The `coord/` directory is the audit trail. One handoff per task, recording the
files changed and why, the commands run with their PASS/FAIL output, the
assumptions made and how they were verified, and the risks left open. Fifteen
handoffs cover the four development waves listed above.

For regulated work — e-invoicing, tax data, compliance — being able to show
*how* a system was built matters as much as showing that it works. The
methodology is documented separately in
[agentic-dev-pipeline](https://github.com/MaurizioLisanti/agentic-dev-pipeline).

## Project status
**Beta.** Tested with synthetic FatturaPA documents checked against the official
schema; not yet used in production. See [Known limitations](#known-limitations-v032).
Part of a broader ecosystem: fatturapa-mcp-server → sdi-ops-monitor

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

- **[agentic-dev-pipeline](https://github.com/MaurizioLisanti/agentic-dev-pipeline)** —
  The governed multi-agent development pipeline this project was built with.
  The handoffs in `coord/` are its output.

---

# Italiano
## Il problema
Ogni progetto che integra FatturaPA
reimplementa da zero la stessa logica
di validazione, parsing e gestione errori SDI.
Il risultato: settimane di lavoro ripetuto,
bug nascosti e nessuna standardizzazione.
## La soluzione
Sette tool AI installabili in una riga —
parsing del documento, rilevamento anomalie sulle
fatture ricevute, report multi-fattura, verifica
P.IVA italiana ed europea via VIES, controlli
strutturali dell'XML e lookup errori SDI offline.

> **Stato: beta.** Leggere i [Limiti noti](#limiti-noti-v032) prima di fare
> affidamento sui risultati della validazione.
## Per chi è
Developer Python e team AI che lavorano
su sistemi di fatturazione elettronica italiana
e vogliono integrare Claude senza reimplementare
la compliance FatturaPA da zero ad ogni progetto.
### Cos'è questo progetto?

Un server [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) che
fornisce agli assistenti AI sette strumenti pronti all'uso per lavorare con le
fatture elettroniche italiane (FatturaPA) e il Sistema di Interscambio (SDI).

### Strumenti disponibili

| Strumento | Input | Cosa fa |
|-----------|-------|---------|
| `validate_invoice` | `xml_content` | Controlla che l'XML sia ben formato e abbia la struttura radice FatturaPA. ⚠️ **Non è ancora una validazione completa contro lo schema** — vedi Limiti noti |
| `extract_invoice_data` | `xml_content` | Estrae fornitore, cliente, importi, righe dettaglio e metadati da un documento FatturaPA valido |
| `lookup_sdi_error` | `error_code` | Restituisce descrizione, categoria e suggerimento di risoluzione per i codici errore SDI (offline). ⚠️ La tabella è in fase di riallineamento con l'elenco ufficiale — vedi Limiti noti |
| `check_piva` | `piva` | Valida una P.IVA italiana tramite l'algoritmo di checksum ufficiale MEF — nessuna chiamata di rete |
| `verify_piva_vies` | `country_code`, `vat_number` | Verifica qualsiasi partita IVA UE contro l'API REST VIES in tempo reale; risponde in modo degradato se il servizio è irraggiungibile |
| `find_invoice_anomalies` | `xml_content` | Rileva anomalie in un documento FatturaPA XML: totale incoerente, IVA errata, data futura, P.IVA invalida, destinatario mancante, righe incomplete, importo negativo, pagamento mancante |
| `generate_invoice_report` | `xml_contents` | Aggrega più documenti FatturaPA XML in un unico report con statistiche, riepilogo fornitori/clienti e analisi delle anomalie |

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
      "args": ["fatturapa-mcp-server"],
      "env": { "FATTURAPA_ALLOWED_ROOTS": "C:\\percorso\\delle\\fatture" }
    }
  }
}
```

`FATTURAPA_ALLOWED_ROOTS` indica le sole cartelle che il server può leggere (separate
da `;` su Windows, da `:` su macOS/Linux). Senza questa variabile ogni lettura da
`file_path` viene rifiutata e le fatture vanno passate come `xml_content`. È una
scelta voluta: il server è pilotato da un agente AI che legge documenti non fidati.

Dopo il riavvio di Claude Desktop, i sette strumenti compariranno nel pannello degli strumenti.

### Limiti noti (v0.3.2)

Un audit contro lo schema ufficiale AdE (FatturaPA v1.2.3) con fatture sintetiche ha
evidenziato i punti seguenti, in correzione nelle prossime release:

- **`validate_invoice` è solo strutturale.** Gli XSD inclusi sono stub: una fattura
  con tipo documento inesistente (`TD99`), divisa non valida (`EURO`) o blocchi
  obbligatori mancanti risulta `valid: true`. Non sostituisce la validazione dello SDI.
- **`lookup_sdi_error`**: alcune descrizioni non corrispondono all'elenco ufficiale
  (es. `00001` è "nome file non valido") e alcuni codici mancano.
- **Lotti**: se un file contiene più fatture, solo la prima viene analizzata del tutto.
- **Encoding**: XML dichiarati ISO-8859-1 / windows-1252 possono essere decodificati male.
- **`.p7m`**: i file firmati non sono ancora supportati; estrarre prima l'XML.
- **Report**: le note di credito (TD04) vengono sommate invece che sottratte; totali
  in valute diverse vengono sommati.
- Gli importi sono restituiti come float.

Già solido oggi: controlli di coerenza (totali, IVA, checksum P.IVA, date), accesso
ai file fail-closed, protezione XXE, gestione di VIES quando il servizio non risponde.
## Changelog / Storico release

| Wave | Tool / Funzionalità | Release |
|------|---------------------|---------|
| Wave 1 | `validate_invoice`, `extract_invoice_data`, `lookup_sdi_error`, `check_piva`, `verify_piva_vies` | v0.1.0 |
| Wave 2 | Pubblicazione PyPI, CI/CD, security audit, coverage completa | v0.1.0 |
| Wave 3 | Propagazione contesto, logging strutturato, progress reporting, accesso file sicuro via roots | v0.1.x |
| Wave 4 | `find_invoice_anomalies`, `generate_invoice_report` | v0.2.0 |

**Statistiche v0.3.2:** 7 tool · 181 test · 95% di coverage, avvio del server incluso

## Cosa dimostra tecnicamente
- MCP server con strict typing mypy, testato su Python 3.11, 3.12 e 3.13
- Security audit automatico — bandit + pip-audit
- Coverage minima garantita all'80% (attualmente 95% su 181 test)
- Accesso al filesystem fail-closed: le letture sono negate salvo configurazione esplicita
- Pubblicato su PyPI — installabile ovunque con una riga
- Bilingue IT/EN — pensato per mercato italiano e internazionale

### Tracciabilita by design

Ogni funzionalita di questo repository e stata costruita con una pipeline
multi-agente governata — planner, executor e reviewer come ruoli distinti,
ciascuno con autorita dichiarata e quality gate obbligatori tra una fase e
l'altra.

La cartella `coord/` e la pista di controllo. Un handoff per task, con i file
modificati e il motivo, i comandi eseguiti con esito PASS/FAIL, le assunzioni
fatte e come sono state verificate, i rischi lasciati aperti. Quindici handoff
coprono le quattro wave di sviluppo elencate sopra.

Nel lavoro su ambiti regolati — fatturazione elettronica, dati fiscali,
compliance — poter mostrare *come* un sistema e stato costruito conta quanto
mostrare che funziona. La metodologia e documentata separatamente in
[agentic-dev-pipeline](https://github.com/MaurizioLisanti/agentic-dev-pipeline).
## Stato del progetto
**Beta.** Testato con fatture FatturaPA sintetiche verificate contro lo schema
ufficiale; non ancora usato in produzione. Vedi [Limiti noti](#limiti-noti-v032).
Parte di un ecosistema più ampio: fatturapa-mcp-server → sdi-ops-monitor

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

- **[agentic-dev-pipeline](https://github.com/MaurizioLisanti/agentic-dev-pipeline)** —
  La pipeline di sviluppo multi-agente governata con cui questo progetto è stato
  costruito. Gli handoff in `coord/` ne sono l'output.

---

## License / Licenza

[MIT](LICENSE)
