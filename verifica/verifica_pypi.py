"""
Verifica del pacchetto pubblicato su PyPI, come lo usa un utente.

Si esegue nello stesso ambiente in cui è installato `fatturapa-mcp-server` (da PyPI):
    pip install fatturapa-mcp-server
    python verifica/verifica_pypi.py

Avvia il server via MCP stdio con un client vero, gli passa fatture INVENTATE
(aziende e P.IVA fittizie) e confronta ogni risposta con il risultato atteso.

Ogni controllo ha uno stato atteso:
  - "ok"          deve funzionare: se fallisce è una REGRESSIONE e il job diventa rosso;
  - "limite noto" difetto noto e dichiarato: non fa fallire il job, ma resta visibile;
  - "bug noto"    difetto noto, da correggere: come sopra.
Se un limite o un bug noto risulta risolto, il job lo segnala (avviso) per aggiornare
lo stato atteso in questo file.

Nessun dato reale, nessun segreto, nessuna chiamata a servizi esterni (VIES escluso).
"""
from __future__ import annotations

import asyncio
import importlib.metadata
import json
import os
import sys
import tempfile
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Callable

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PACCHETTO = "fatturapa-mcp-server"


# ------------------------------------------------------------------ fatture inventate
def piva_valida(base10: str) -> str:
    """Aggiunge la cifra di controllo MEF a 10 cifre."""
    s = 0
    for i, c in enumerate(base10):
        n = int(c)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        s += n
    return base10 + str((10 - s % 10) % 10)


CED = piva_valida("0123456789")  # 01234567897, inventata
CES = piva_valida("0987654321")  # 09876543217, inventata
PIVA_ERRATA = CED[:-1] + str((int(CED[-1]) + 1) % 10)
FUTURO = (date.today() + timedelta(days=60)).isoformat()
NS = "http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.2"


def _body(tipo="TD01", numero="1", data="2026-09-15", righe=((100.00, 22.00),), totale=None, senza_data=False):
    linee, riep = [], {}
    for i, (imp, aliq) in enumerate(righe, 1):
        linee.append(
            f"<DettaglioLinee><NumeroLinea>{i}</NumeroLinea><Descrizione>Servizio di prova {i}</Descrizione>"
            f"<Quantita>1.00</Quantita><PrezzoUnitario>{imp:.2f}</PrezzoUnitario><PrezzoTotale>{imp:.2f}</PrezzoTotale>"
            f"<AliquotaIVA>{aliq:.2f}</AliquotaIVA></DettaglioLinee>"
        )
        riep[aliq] = riep.get(aliq, 0) + imp
    riepilogo = "".join(
        f"<DatiRiepilogo><AliquotaIVA>{a:.2f}</AliquotaIVA><ImponibileImporto>{v:.2f}</ImponibileImporto>"
        f"<Imposta>{v * a / 100:.2f}</Imposta></DatiRiepilogo>"
        for a, v in riep.items()
    )
    tot = sum(v + v * a / 100 for a, v in riep.items()) if totale is None else totale
    d = "" if senza_data else f"<Data>{data}</Data>"
    return (
        "<FatturaElettronicaBody><DatiGenerali><DatiGeneraliDocumento>"
        f"<TipoDocumento>{tipo}</TipoDocumento><Divisa>EUR</Divisa>{d}<Numero>{numero}</Numero>"
        f"<ImportoTotaleDocumento>{tot:.2f}</ImportoTotaleDocumento></DatiGeneraliDocumento></DatiGenerali>"
        f"<DatiBeniServizi>{''.join(linee)}{riepilogo}</DatiBeniServizi></FatturaElettronicaBody>"
    )


def fattura(bodies, piva_ced=CED) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<p:FatturaElettronica versione="FPR12" xmlns:p="{NS}" xmlns:ds="http://www.w3.org/2000/09/xmldsig#">
<FatturaElettronicaHeader>
<DatiTrasmissione><IdTrasmittente><IdPaese>IT</IdPaese><IdCodice>{piva_ced}</IdCodice></IdTrasmittente><ProgressivoInvio>00001</ProgressivoInvio><FormatoTrasmissione>FPR12</FormatoTrasmissione><CodiceDestinatario>0000000</CodiceDestinatario></DatiTrasmissione>
<CedentePrestatore><DatiAnagrafici><IdFiscaleIVA><IdPaese>IT</IdPaese><IdCodice>{piva_ced}</IdCodice></IdFiscaleIVA><Anagrafica><Denominazione>Officina Esempio Srl</Denominazione></Anagrafica><RegimeFiscale>RF01</RegimeFiscale></DatiAnagrafici>
<Sede><Indirizzo>Via Inventata 1</Indirizzo><CAP>00100</CAP><Comune>Roma</Comune><Provincia>RM</Provincia><Nazione>IT</Nazione></Sede></CedentePrestatore>
<CessionarioCommittente><DatiAnagrafici><IdFiscaleIVA><IdPaese>IT</IdPaese><IdCodice>{CES}</IdCodice></IdFiscaleIVA><Anagrafica><Denominazione>Cliente Fittizio Spa</Denominazione></Anagrafica></DatiAnagrafici>
<Sede><Indirizzo>Piazza Prova 2</Indirizzo><CAP>20100</CAP><Comune>Milano</Comune><Provincia>MI</Provincia><Nazione>IT</Nazione></Sede></CessionarioCommittente>
</FatturaElettronicaHeader>
{''.join(bodies)}
</p:FatturaElettronica>"""


XML = {
    "corretta": fattura([_body()]),
    "totale": fattura([_body(totale=150.00)]),
    "piva": fattura([_body()], piva_ced=PIVA_ERRATA),
    "td99": fattura([_body(tipo="TD99")]),
    "futura": fattura([_body(data=FUTURO)]),
    "senza_data": fattura([_body(senza_data=True)]),
    "lotto": fattura([_body(numero="1"), _body(numero="2", righe=((200.00, 22.00),))]),
    "nota_credito": fattura([_body(tipo="TD04", numero="NC1", righe=((40.00, 22.00),))]),
}


# ------------------------------------------------------------------ helper
def _risposta(res) -> Any:
    if res.isError:
        return {"_errore_tool": " ".join(c.text for c in res.content if hasattr(c, "text"))}
    if res.structuredContent is not None:
        return res.structuredContent
    testo = " ".join(c.text for c in res.content if hasattr(c, "text"))
    try:
        return json.loads(testo)
    except Exception:
        return testo


def codici(r: Any, severita: str | None = None) -> set[str]:
    if not isinstance(r, dict):
        return set()
    return {a.get("code") for a in r.get("anomalies", []) if severita is None or a.get("severity") == severita}


def non_valida(r: Any) -> bool:
    return isinstance(r, dict) and r.get("valid") is False


def errore_tool(r: Any) -> bool:
    return isinstance(r, dict) and "_errore_tool" in r


@dataclass
class Controllo:
    nome: str
    atteso: str  # "ok" | "limite noto" | "bug noto"
    tool: str
    args: dict
    giudica: Callable[[Any], bool]
    nota: str = ""


CONTROLLI = [
    # --- validazione e anomalie
    Controllo("Fattura corretta: nessun errore", "ok", "find_invoice_anomalies", {"xml_content": XML["corretta"]},
              lambda r: not codici(r, "error") and not errore_tool(r)),
    Controllo("Totale incoerente (150 vs 122): TOTAL_MISMATCH", "ok", "find_invoice_anomalies", {"xml_content": XML["totale"]},
              lambda r: "TOTAL_MISMATCH" in codici(r)),
    Controllo("P.IVA del fornitore errata: INVALID_PIVA", "ok", "find_invoice_anomalies", {"xml_content": XML["piva"]},
              lambda r: "INVALID_PIVA" in codici(r)),
    Controllo("Data futura: FUTURE_DATE", "ok", "find_invoice_anomalies", {"xml_content": XML["futura"]},
              lambda r: "FUTURE_DATE" in codici(r)),
    Controllo("TD99 rifiutato dalla validazione", "limite noto", "validate_invoice", {"xml_content": XML["td99"]},
              non_valida, "validazione strutturale, non lo schema ufficiale"),
    Controllo("Data mancante rifiutata dalla validazione", "limite noto", "validate_invoice", {"xml_content": XML["senza_data"]},
              non_valida, "validazione strutturale, non lo schema ufficiale"),
    # --- estrazione e report
    Controllo("Nota di credito letta come TD04", "ok", "extract_invoice_data", {"xml_content": XML["nota_credito"]},
              lambda r: isinstance(r, dict) and r.get("document_type") == "TD04" and abs(float(r.get("total_amount") or 0) - 48.80) < 0.01),
    Controllo("Lotto: le righe della seconda fattura non finiscono nella prima", "limite noto", "extract_invoice_data", {"xml_content": XML["lotto"]},
              lambda r: isinstance(r, dict) and len(r.get("line_items", [])) == 1, "lotti con più fatture non gestiti"),
    Controllo("Report fattura 122,00 + nota di credito 48,80 = 73,20", "bug noto", "generate_invoice_report",
              {"xml_contents": [XML["corretta"], XML["nota_credito"]], "title": "verifica"},
              lambda r: isinstance(r, dict) and abs(float(r.get("total_amount") or 0) - 73.20) < 0.01, "la nota di credito viene sommata"),
    # --- partite IVA
    Controllo("check_piva: P.IVA valida", "ok", "check_piva", {"piva": CED}, lambda r: isinstance(r, dict) and r.get("valid") is True),
    Controllo("check_piva: cifra di controllo errata", "ok", "check_piva", {"piva": PIVA_ERRATA}, lambda r: isinstance(r, dict) and r.get("valid") is False),
    Controllo("check_piva: prefisso IT accettato", "ok", "check_piva", {"piva": "IT" + CED}, lambda r: isinstance(r, dict) and r.get("valid") is True),
    Controllo("check_piva: troppo corta", "ok", "check_piva", {"piva": "123"}, lambda r: isinstance(r, dict) and r.get("valid") is False),
    Controllo("check_piva: tutti zeri rifiutata", "bug noto", "check_piva", {"piva": "00000000000"},
              lambda r: isinstance(r, dict) and r.get("valid") is False),
    Controllo("check_piva: caratteri non ASCII rifiutati senza errore interno", "bug noto", "check_piva", {"piva": "²" * 11},
              lambda r: isinstance(r, dict) and r.get("valid") is False, "str.isdigit() accetta '²'"),
    # --- codici SDI
    Controllo("lookup_sdi_error: 00200 restituisce una descrizione", "ok", "lookup_sdi_error", {"error_code": "00200"},
              lambda r: isinstance(r, dict) and bool(r.get("description"))),
    Controllo("lookup_sdi_error: 00404 (fattura duplicata) presente", "limite noto", "lookup_sdi_error", {"error_code": "00404"},
              lambda r: isinstance(r, dict) and bool(r.get("description")), "tabella SDI incompleta"),
]


# ------------------------------------------------------------------ esecuzione
def comando_server() -> str:
    bin_dir = Path(sys.executable).parent
    nome = "fatturapa-mcp-server.exe" if os.name == "nt" else "fatturapa-mcp-server"
    exe = bin_dir / nome
    return str(exe) if exe.exists() else nome


async def esegui() -> dict:
    versione_pacchetto = importlib.metadata.version(PACCHETTO)
    env = {k: v for k, v in os.environ.items() if k != "FATTURAPA_ALLOWED_ROOTS"}
    risultati = []
    with tempfile.TemporaryDirectory() as tmp:
        fuori_root = Path(tmp) / "fattura.xml"
        fuori_root.write_text(XML["corretta"], encoding="utf-8")
        params = StdioServerParameters(command=comando_server(), args=[], env=env)
        async with stdio_client(params) as (r, w):
            async with ClientSession(r, w) as s:
                init = await s.initialize()
                tools = (await s.list_tools()).tools

                def aggiungi(nome, atteso, passato, dettaglio, nota=""):
                    risultati.append({"nome": nome, "atteso": atteso, "passato": bool(passato), "dettaglio": dettaglio, "nota": nota})

                aggiungi("Handshake: versione dichiarata = versione del pacchetto", "ok",
                         init.serverInfo.version == versione_pacchetto,
                         f"dichiarata {init.serverInfo.version}, pacchetto {versione_pacchetto}")
                aggiungi("7 tool esposti", "ok", len(tools) == 7, f"{len(tools)} tool: {', '.join(t.name for t in tools)}")

                for c in CONTROLLI:
                    try:
                        r = _risposta(await s.call_tool(c.tool, c.args))
                        passato = c.giudica(r)
                    except Exception as e:  # il server non risponde o cade
                        r, passato = {"_eccezione": repr(e)}, False
                    aggiungi(c.nome, c.atteso, passato, json.dumps(r, ensure_ascii=False)[:300], c.nota)

                # Sicurezza: senza FATTURAPA_ALLOWED_ROOTS la lettura di file deve essere rifiutata
                r = _risposta(await s.call_tool("validate_invoice", {"file_path": str(fuori_root)}))
                aggiungi("Sandbox: lettura di file rifiutata senza cartelle consentite", "ok", errore_tool(r),
                         json.dumps(r, ensure_ascii=False)[:300])
    return {"versione": versione_pacchetto, "python": sys.version.split()[0], "risultati": risultati}


def esito(x: dict) -> str:
    if x["atteso"] == "ok":
        return "✅ ok" if x["passato"] else "❌ REGRESSIONE"
    return "🎉 risolto: aggiornare lo stato atteso" if x["passato"] else f"⚠️ {x['atteso']}"


def riepilogo(dati: dict) -> tuple[str, int, int]:
    righe = dati["risultati"]
    regressioni = [x for x in righe if x["atteso"] == "ok" and not x["passato"]]
    risolti = [x for x in righe if x["atteso"] != "ok" and x["passato"]]
    ok = sum(1 for x in righe if x["atteso"] == "ok" and x["passato"])
    noti = sum(1 for x in righe if x["atteso"] != "ok" and not x["passato"])
    md = [
        f"## fatturapa-mcp-server {dati['versione']} da PyPI · Python {dati['python']}",
        "",
        f"**{ok} controlli ok · {noti} limiti/bug noti · {len(regressioni)} regressioni · {len(risolti)} risolti**",
        "",
        "Fatture e partite IVA inventate. Il job fallisce solo per una regressione.",
        "",
        "| Controllo | Esito | Nota |",
        "|---|---|---|",
    ]
    md += [f"| {x['nome']} | {esito(x)} | {x['nota']} |" for x in righe]
    return "\n".join(md) + "\n", len(regressioni), len(risolti)


def main() -> int:
    dati = asyncio.run(esegui())
    md, n_regressioni, n_risolti = riepilogo(dati)
    print(md)
    for x in dati["risultati"]:
        if x["atteso"] == "ok" and not x["passato"]:
            print(f"   ↳ {x['nome']}: {x['dettaglio']}")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:  # su GitHub Actions: tabella visibile nella pagina del job
        with open(summary, "a", encoding="utf-8") as f:
            f.write(md)
    if n_risolti and os.environ.get("GITHUB_ACTIONS"):
        print(f"::notice::{n_risolti} limiti o bug noti risultano risolti: aggiornare lo stato atteso in verifica/verifica_pypi.py")
    return 1 if n_regressioni else 0


if __name__ == "__main__":
    sys.exit(main())
