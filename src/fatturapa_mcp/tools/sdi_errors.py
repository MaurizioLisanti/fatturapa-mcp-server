"""
fatturapa_mcp.tools.sdi_errors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
MCP tool: lookup_sdi_error — looks up SDI (Sistema di Interscambio) error codes.
"""

from typing import TypedDict

# ---------------------------------------------------------------------------
# Static error table — sourced from AdE "Allegato C" (technical specifications
# for the Sistema di Interscambio, FatturaPA electronic invoicing).
# ---------------------------------------------------------------------------

_UNKNOWN_SENTINEL = "__unknown__"


class _ErrorEntry(TypedDict):
    description: str
    category: str
    resolution: str


_SDI_ERRORS: dict[str, _ErrorEntry] = {
    # ── STRUTTURA ────────────────────────────────────────────────────────────
    "00001": {
        "description": "File già ricevuto dal Sistema di Interscambio.",
        "category": "STRUTTURA",
        "resolution": (
            "Verificare se la fattura è già stata trasmessa con successo. "
            "Non reinviare il file; consultare la ricevuta originale."
        ),
    },
    "00002": {
        "description": (
            "Prevalidazione non superata: il nome del file non rispetta le convenzioni "
            "oppure la dimensione del file supera il limite ammesso."
        ),
        "category": "STRUTTURA",
        "resolution": (
            "Verificare che il nome file rispetti il formato "
            "<IdPaese><IdCodice>_<Progressivo>.<Estensione> "
            "e che la dimensione non superi 5 MB."
        ),
    },
    "00003": {
        "description": "Il file risulta già ricevuto con lo stesso hash.",
        "category": "STRUTTURA",
        "resolution": (
            "Il contenuto del file è identico a uno già trasmesso. "
            "Se la fattura deve essere ri-emessa, correggerla e assegnarle "
            "un nuovo numero."
        ),
    },
    # ── CONTENUTO ────────────────────────────────────────────────────────────
    "00100": {
        "description": (
            "Il Cedente/Prestatore non è presente nell'Anagrafe Tributaria "
            "come soggetto passivo IVA."
        ),
        "category": "CONTENUTO",
        "resolution": (
            "Verificare la partita IVA del Cedente/Prestatore e accertarsi "
            "che sia attiva presso l'Agenzia delle Entrate."
        ),
    },
    "00101": {
        "description": "La partita IVA del Cedente/Prestatore non è valida.",
        "category": "CONTENUTO",
        "resolution": (
            "Controllare il campo IdCodice del Cedente/Prestatore. "
            "La P.IVA deve essere di 11 cifre e superare il controllo di checksum."
        ),
    },
    "00102": {
        "description": (
            "Il codice fiscale del Cedente/Prestatore non è valido "
            "o non corrisponde alla partita IVA indicata."
        ),
        "category": "CONTENUTO",
        "resolution": (
            "Allineare CodiceFiscale e IdCodice del Cedente/Prestatore. "
            "Verificare i dati nell'Anagrafe Tributaria."
        ),
    },
    "00103": {
        "description": (
            "Il codice destinatario (CodiceDestinatario) non è censito nel Sistema "
            "di Interscambio o non è abilitato alla ricezione."
        ),
        "category": "CONTENUTO",
        "resolution": (
            "Verificare il CodiceDestinatario con il cliente. Se il destinatario usa "
            "PEC, inserire '0000000' come CodiceDestinatario e valorizzare "
            "PECDestinatario."
        ),
    },
    "00104": {
        "description": "La partita IVA del Cessionario/Committente non è valida.",
        "category": "CONTENUTO",
        "resolution": (
            "Controllare il campo IdCodice del Cessionario/Committente. "
            "La P.IVA deve essere di 11 cifre e superare il controllo di checksum."
        ),
    },
    "00105": {
        "description": "Il codice fiscale del Cessionario/Committente non è valido.",
        "category": "CONTENUTO",
        "resolution": (
            "Verificare il CodiceFiscale del Cessionario/Committente "
            "nell'Anagrafe Tributaria."
        ),
    },
    "00106": {
        "description": (
            "Il numero del documento (Numero) contiene caratteri non ammessi "
            "o non rispetta il formato previsto."
        ),
        "category": "CONTENUTO",
        "resolution": (
            "Utilizzare solo caratteri alfanumerici e i simboli ammessi "
            "dallo schema XSD. La lunghezza massima è 20 caratteri."
        ),
    },
    "00107": {
        "description": (
            "La data del documento (Data) è antecedente al 1° gennaio dell'anno "
            "di riferimento, futura rispetto alla data di trasmissione, "
            "o non è in formato YYYY-MM-DD."
        ),
        "category": "CONTENUTO",
        "resolution": (
            "Correggere il campo Data nella sezione DatiGeneraliDocumento "
            "assicurandosi che sia nel formato ISO 8601 (YYYY-MM-DD) e coerente "
            "con il periodo di imposta corrente."
        ),
    },
    "00108": {
        "description": (
            "L'importo totale del documento (ImportoTotaleDocumento) non è congruente "
            "con la somma di imponibili e imposte."
        ),
        "category": "CONTENUTO",
        "resolution": (
            "Ricalcolare ImportoTotaleDocumento come somma di ImponibileImporto "
            "e Imposta per ogni aliquota in DatiRiepilogo."
        ),
    },
    "00109": {
        "description": (
            "Differenza rilevata tra imponibili, imposte e totale documento: "
            "i valori non risultano coerenti tra loro."
        ),
        "category": "CONTENUTO",
        "resolution": (
            "Verificare la coerenza tra DatiRiepilogo, DatiBeniServizi e "
            "ImportoTotaleDocumento. Prestare attenzione agli arrotondamenti."
        ),
    },
    "00110": {
        "description": (
            "L'aliquota IVA o la Natura dell'operazione non è corretta, "
            "è mancante o non è ammessa per il tipo documento indicato."
        ),
        "category": "CONTENUTO",
        "resolution": (
            "Verificare che ogni riga con IVA a zero riporti il codice Natura corretto "
            "(N1–N7). Per operazioni imponibili indicare l'aliquota percentuale."
        ),
    },
    "00111": {
        "description": (
            "Il tipo documento (TipoDocumento) non è coerente con i dati fiscali "
            "presenti nel file (es. nota di credito con importo positivo)."
        ),
        "category": "CONTENUTO",
        "resolution": (
            "Controllare che TipoDocumento (TD01–TD28) corrisponda alla natura "
            "giuridica dell'operazione e al segno degli importi."
        ),
    },
    "00115": {
        "description": (
            "Fattura duplicata: esiste già nel Sistema di Interscambio una fattura "
            "dello stesso Cedente/Prestatore con lo stesso numero e data documento."
        ),
        "category": "CONTENUTO",
        "resolution": (
            "Assegnare un numero documento univoco oppure verificare se la fattura "
            "è già stata correttamente inviata e ricevuta."
        ),
    },
    "00116": {
        "description": (
            "Il progressivo numerico del file non è corretto "
            "rispetto all'ultimo progressivo registrato per il soggetto trasmittente."
        ),
        "category": "CONTENUTO",
        "resolution": (
            "Allineare il progressivo nel nome file con il contatore gestito "
            "dal sistema di trasmissione; evitare buchi o duplicati nella sequenza."
        ),
    },
    # ── FIRMA ────────────────────────────────────────────────────────────────
    "00200": {
        "description": (
            "Firma digitale assente: il file XML non risulta firmato "
            "oppure la firma non è riconoscibile."
        ),
        "category": "FIRMA",
        "resolution": (
            "Firmare il file con un certificato qualificato in formato CAdES-BES (P7M) "
            "o XAdES-BES prima della trasmissione."
        ),
    },
    "00201": {
        "description": "Verifica della firma digitale non riuscita.",
        "category": "FIRMA",
        "resolution": (
            "Controllare l'integrità del file: potrebbe essere stato corrotto o "
            "modificato dopo la firma. Ri-firmare il file originale."
        ),
    },
    "00202": {
        "description": "Il certificato di firma digitale risulta scaduto.",
        "category": "FIRMA",
        "resolution": (
            "Rinnovare il certificato di firma qualificata presso un prestatore "
            "di servizi fiduciari qualificato (QTSP), quindi ri-firmare "
            "e ritrasmettere."
        ),
    },
    "00203": {
        "description": "Il certificato di firma digitale risulta revocato.",
        "category": "FIRMA",
        "resolution": (
            "Il certificato è stato revocato dal QTSP emittente. "
            "Ottenere un nuovo certificato di firma qualificata e ri-firmare il file."
        ),
    },
    "00204": {
        "description": (
            "Il certificato di firma digitale non è ancora valido "
            "(data di inizio validità futura)."
        ),
        "category": "FIRMA",
        "resolution": (
            "Attendere che il certificato diventi valido oppure utilizzare "
            "un certificato già attivo."
        ),
    },
    "00205": {
        "description": (
            "Il certificato di firma digitale non è stato rilasciato da una "
            "Certification Authority riconosciuta nell'elenco di fiducia (TSL) europeo."
        ),
        "category": "FIRMA",
        "resolution": (
            "Utilizzare un certificato qualificato rilasciato da un QTSP "
            "incluso nell'elenco eIDAS della Commissione Europea."
        ),
    },
    "00206": {
        "description": (
            "Formato file non supportato: il Sistema di Interscambio accetta "
            "solo file XML (non firmati) o P7M (XML firmati CAdES)."
        ),
        "category": "FIRMA",
        "resolution": (
            "Trasmettere il file nel formato corretto: XML senza firma "
            "oppure XML.P7M con firma CAdES-BES."
        ),
    },
    "00207": {
        "description": "Algoritmo di firma non ammesso dal Sistema di Interscambio.",
        "category": "FIRMA",
        "resolution": (
            "Utilizzare SHA-256 come algoritmo di hashing nella firma CAdES. "
            "Algoritmi obsoleti come SHA-1 non sono ammessi."
        ),
    },
    # ── RECAPITO ─────────────────────────────────────────────────────────────
    "00300": {
        "description": (
            "Recapito non effettuato: impossibilità temporanea di consegnare "
            "il documento al destinatario per indisponibilità del canale."
        ),
        "category": "RECAPITO",
        "resolution": (
            "Il SdI ha tentato la consegna per 10 giorni senza successo. "
            "Il documento è comunque disponibile nell'area riservata del destinatario "
            "sul portale Fatture e Corrispettivi."
        ),
    },
    "00301": {
        "description": (
            "Recapito non effettuato: l'indirizzo PEC del destinatario "
            "non è valido o non è raggiungibile."
        ),
        "category": "RECAPITO",
        "resolution": (
            "Verificare con il destinatario l'indirizzo PEC corretto "
            "e aggiornare il campo PECDestinatario. "
            "In alternativa, usare CodiceDestinatario se disponibile."
        ),
    },
    "00302": {
        "description": (
            "Recapito non effettuato: la casella PEC del destinatario è piena "
            "e non accetta nuovi messaggi."
        ),
        "category": "RECAPITO",
        "resolution": (
            "Contattare il destinatario affinché liberi spazio nella casella PEC. "
            "Il documento è consultabile nell'area riservata del portale AdE."
        ),
    },
    "00303": {
        "description": (
            "Recapito non effettuato: il servizio di ricezione del destinatario "
            "non è attivo o ha rifiutato la consegna."
        ),
        "category": "RECAPITO",
        "resolution": (
            "Verificare con il destinatario la configurazione del canale di ricezione "
            "(CodiceSDI o PEC). Il documento è accessibile sul portale AdE."
        ),
    },
    "00304": {
        "description": (
            "Recapito non effettuato: il destinatario non è stato trovato "
            "nel sistema SDI con i dati indicati."
        ),
        "category": "RECAPITO",
        "resolution": (
            "Controllare CodiceDestinatario e/o PECDestinatario. "
            "Per privati o soggetti senza codice SDI, usare "
            "CodiceDestinatario='0000000'."
        ),
    },
}


class LookupResult(TypedDict):
    """Structured result returned by lookup_sdi_error."""

    code: str
    description: str
    category: str
    resolution: str


def lookup_sdi_error(error_code: str) -> LookupResult:
    """Look up an SDI error code and return its human-readable description.

    Uses a local static table of official AdE error codes.
    No network call required.

    Args:
        error_code: SDI error code string (e.g., "00001", "00002").

    Returns:
        A LookupResult with keys:
            code (str): The queried error code.
            description (str): Official Italian description.
            category (str): Error category (e.g., "STRUTTURA", "CONTENUTO").
            resolution (str): Suggested resolution hint.

    Raises:
        ValueError: If *error_code* is not found in the known error table.
    """
    entry = _SDI_ERRORS.get(error_code)
    if entry is None:
        raise ValueError(f"Unknown SDI error code: {error_code!r}")
    return LookupResult(
        code=error_code,
        description=entry["description"],
        category=entry["category"],
        resolution=entry["resolution"],
    )
