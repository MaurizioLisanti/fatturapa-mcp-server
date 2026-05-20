"""Tests for the find_invoice_anomalies tool."""

import os
from pathlib import Path

import pytest

from fatturapa_mcp.tools.anomalies import find_invoice_anomalies
from tests.conftest import MockCtx

_NS_V13 = "http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.3"

# P.IVA values — checksum-verified:
#   "12345678903": s_odd=25, s_even=22, check=3 ✓
#   "98765432103": s_odd=25, s_even=22, check=3 ✓
#   "12345678901": s_odd=25, s_even=22, check=3, actual=1 → INVALID
_VALID_PIVA_SUPPLIER = "12345678903"
_VALID_PIVA_CUSTOMER = "98765432103"
_INVALID_PIVA = "12345678901"


def _build_xml(
    piva_supplier: str = _VALID_PIVA_SUPPLIER,
    piva_customer: str = _VALID_PIVA_CUSTOMER,
    date_str: str = "2024-01-15",
    dest_code: str | None = "AAAAAAA",
    total: str = "122.00",
    imponibile: str = "100.00",
    imposta: str = "22.00",
    doc_type: str = "TD01",
    include_payment: bool = True,
    include_desc: bool = True,
    include_price_total: bool = True,
) -> str:
    """Build a minimal FatturaPA v1.3 XML string with configurable fields."""
    dest_el = (
        f"<CodiceDestinatario>{dest_code}</CodiceDestinatario>"
        if dest_code is not None
        else ""
    )
    payment_el = (
        "<DatiPagamento><CondizioniPagamento>TP02</CondizioniPagamento>"
        "<DettaglioPagamento><ModalitaPagamento>MP05</ModalitaPagamento>"
        f"<ImportoPagamento>{total}</ImportoPagamento></DettaglioPagamento></DatiPagamento>"
        if include_payment
        else ""
    )
    desc_el = "<Descrizione>Servizio di test</Descrizione>" if include_desc else ""
    price_el = (
        f"<PrezzoTotale>{imponibile}</PrezzoTotale>" if include_price_total else ""
    )
    return (
        f'<?xml version="1.0" encoding="UTF-8"?>'
        f'<p:FatturaElettronica xmlns:p="{_NS_V13}" versione="FPR12">'
        "<FatturaElettronicaHeader>"
        "<DatiTrasmissione>"
        f"<IdTrasmittente><IdPaese>IT</IdPaese><IdCodice>{piva_supplier}</IdCodice></IdTrasmittente>"
        "<ProgressivoInvio>00001</ProgressivoInvio>"
        "<FormatoTrasmissione>FPR12</FormatoTrasmissione>"
        f"{dest_el}"
        "</DatiTrasmissione>"
        "<CedentePrestatore><DatiAnagrafici>"
        f"<IdFiscaleIVA><IdPaese>IT</IdPaese><IdCodice>{piva_supplier}</IdCodice></IdFiscaleIVA>"
        "<Anagrafica><Denominazione>Fornitore Srl</Denominazione></Anagrafica>"
        "<RegimeFiscale>RF01</RegimeFiscale>"
        "</DatiAnagrafici>"
        "<Sede><Indirizzo>Via A 1</Indirizzo><CAP>00100</CAP>"
        "<Comune>Roma</Comune><Nazione>IT</Nazione></Sede>"
        "</CedentePrestatore>"
        "<CessionarioCommittente><DatiAnagrafici>"
        f"<IdFiscaleIVA><IdPaese>IT</IdPaese><IdCodice>{piva_customer}</IdCodice></IdFiscaleIVA>"
        "<Anagrafica><Denominazione>Cliente Srl</Denominazione></Anagrafica>"
        "</DatiAnagrafici>"
        "<Sede><Indirizzo>Via B 2</Indirizzo><CAP>20100</CAP>"
        "<Comune>Milano</Comune><Nazione>IT</Nazione></Sede>"
        "</CessionarioCommittente>"
        "</FatturaElettronicaHeader>"
        "<FatturaElettronicaBody>"
        "<DatiGenerali><DatiGeneraliDocumento>"
        f"<TipoDocumento>{doc_type}</TipoDocumento><Divisa>EUR</Divisa>"
        f"<Data>{date_str}</Data><Numero>2024/001</Numero>"
        f"<ImportoTotaleDocumento>{total}</ImportoTotaleDocumento>"
        "</DatiGeneraliDocumento></DatiGenerali>"
        "<DatiBeniServizi>"
        "<DettaglioLinee>"
        "<NumeroLinea>1</NumeroLinea>"
        f"{desc_el}"
        "<Quantita>1.00</Quantita><PrezzoUnitario>100.00</PrezzoUnitario>"
        f"{price_el}"
        "<AliquotaIVA>22.00</AliquotaIVA>"
        "</DettaglioLinee>"
        "<DatiRiepilogo>"
        "<AliquotaIVA>22.00</AliquotaIVA>"
        f"<ImponibileImporto>{imponibile}</ImponibileImporto>"
        f"<Imposta>{imposta}</Imposta>"
        "<EsigibilitaIVA>I</EsigibilitaIVA>"
        "</DatiRiepilogo>"
        "</DatiBeniServizi>"
        f"{payment_el}"
        "</FatturaElettronicaBody>"
        "</p:FatturaElettronica>"
    )


_CLEAN_XML = _build_xml()


class TestFindInvoiceAnomaliesClean:
    """A well-formed invoice must produce no anomalies."""

    async def test_clean_invoice_is_clean(self) -> None:
        """Clean XML with all checks passing returns is_clean=True."""
        result = await find_invoice_anomalies(_CLEAN_XML)
        assert result["is_clean"] is True
        assert result["anomalies_found"] == 0
        assert result["anomalies"] == []
        assert result["errors"] == []
        assert result["warnings"] == []

    async def test_result_has_all_required_keys(self) -> None:
        """Result TypedDict contains all five expected keys."""
        result = await find_invoice_anomalies(_CLEAN_XML)
        assert "anomalies_found" in result
        assert "anomalies" in result
        assert "warnings" in result
        assert "errors" in result
        assert "is_clean" in result


class TestFindInvoiceAnomaliesDetection:
    """Each anomaly category is independently detected."""

    async def test_total_mismatch(self) -> None:
        """ImportoTotaleDocumento != sum of DatiRiepilogo yields TOTAL_MISMATCH."""
        xml = _build_xml(total="200.00")  # sum(100+22)=122 ≠ 200
        result = await find_invoice_anomalies(xml)
        codes = [a["code"] for a in result["anomalies"]]
        assert "TOTAL_MISMATCH" in codes
        error = next(a for a in result["errors"] if a["code"] == "TOTAL_MISMATCH")
        assert error["severity"] == "error"

    async def test_vat_mismatch(self) -> None:
        """AliquotaIVA*imponibile != imposta yields VAT_MISMATCH error."""
        xml = _build_xml(imposta="30.00")  # 22% of 100 = 22 ≠ 30
        result = await find_invoice_anomalies(xml)
        codes = [a["code"] for a in result["anomalies"]]
        assert "VAT_MISMATCH" in codes
        vat_err = next(a for a in result["errors"] if a["code"] == "VAT_MISMATCH")
        assert vat_err["severity"] == "error"

    async def test_future_date(self) -> None:
        """An invoice dated in the future yields FUTURE_DATE warning."""
        xml = _build_xml(date_str="2099-12-31")
        result = await find_invoice_anomalies(xml)
        codes = [a["code"] for a in result["anomalies"]]
        assert "FUTURE_DATE" in codes
        fd_warn = next(a for a in result["warnings"] if a["code"] == "FUTURE_DATE")
        assert fd_warn["severity"] == "warning"

    async def test_invalid_piva_supplier(self) -> None:
        """An invalid supplier P.IVA (wrong checksum) yields INVALID_PIVA error."""
        xml = _build_xml(piva_supplier=_INVALID_PIVA)
        result = await find_invoice_anomalies(xml)
        codes = [a["code"] for a in result["anomalies"]]
        assert "INVALID_PIVA" in codes
        piva_errors = [a for a in result["errors"] if a["code"] == "INVALID_PIVA"]
        assert any("fornitore" in a["detail"] for a in piva_errors)

    async def test_invalid_piva_customer(self) -> None:
        """An invalid customer P.IVA (wrong checksum) yields INVALID_PIVA error."""
        xml = _build_xml(piva_customer=_INVALID_PIVA)
        result = await find_invoice_anomalies(xml)
        codes = [a["code"] for a in result["anomalies"]]
        assert "INVALID_PIVA" in codes
        piva_errors = [a for a in result["errors"] if a["code"] == "INVALID_PIVA"]
        assert any("cliente" in a["detail"] for a in piva_errors)

    async def test_missing_dest_code(self) -> None:
        """Absent CodiceDestinatario yields MISSING_DEST_CODE warning."""
        xml = _build_xml(dest_code=None)
        result = await find_invoice_anomalies(xml)
        codes = [a["code"] for a in result["anomalies"]]
        assert "MISSING_DEST_CODE" in codes
        w = next(a for a in result["warnings"] if a["code"] == "MISSING_DEST_CODE")
        assert w["severity"] == "warning"

    async def test_suspicious_dest_code(self) -> None:
        """CodiceDestinatario='0000000' is treated as suspicious."""
        xml = _build_xml(dest_code="0000000")
        result = await find_invoice_anomalies(xml)
        codes = [a["code"] for a in result["anomalies"]]
        assert "MISSING_DEST_CODE" in codes

    async def test_incomplete_line_missing_description(self) -> None:
        """A line item without Descrizione yields INCOMPLETE_LINE warning."""
        xml = _build_xml(include_desc=False)
        result = await find_invoice_anomalies(xml)
        codes = [a["code"] for a in result["anomalies"]]
        assert "INCOMPLETE_LINE" in codes
        w = next(a for a in result["warnings"] if a["code"] == "INCOMPLETE_LINE")
        assert "Descrizione" in w["detail"]

    async def test_incomplete_line_missing_price(self) -> None:
        """A line item without PrezzoTotale yields INCOMPLETE_LINE warning."""
        xml = _build_xml(include_price_total=False)
        result = await find_invoice_anomalies(xml)
        codes = [a["code"] for a in result["anomalies"]]
        assert "INCOMPLETE_LINE" in codes
        w = next(a for a in result["warnings"] if a["code"] == "INCOMPLETE_LINE")
        assert "PrezzoTotale" in w["detail"]

    async def test_negative_amount_not_td04(self) -> None:
        """Negative total on a non-credit-note type yields NEGATIVE_AMOUNT warning."""
        xml = _build_xml(
            total="-122.00", imponibile="-100.00", imposta="-22.00", doc_type="TD01"
        )
        result = await find_invoice_anomalies(xml)
        codes = [a["code"] for a in result["anomalies"]]
        assert "NEGATIVE_AMOUNT" in codes
        assert "TOTAL_MISMATCH" not in codes

    async def test_negative_amount_td04_allowed(self) -> None:
        """Negative total on TD04 (credit note) does NOT yield NEGATIVE_AMOUNT."""
        xml = _build_xml(
            total="-122.00", imponibile="-100.00", imposta="-22.00", doc_type="TD04"
        )
        result = await find_invoice_anomalies(xml)
        codes = [a["code"] for a in result["anomalies"]]
        assert "NEGATIVE_AMOUNT" not in codes

    async def test_missing_payment(self) -> None:
        """No DatiPagamento element yields MISSING_PAYMENT warning."""
        xml = _build_xml(include_payment=False)
        result = await find_invoice_anomalies(xml)
        codes = [a["code"] for a in result["anomalies"]]
        assert "MISSING_PAYMENT" in codes
        w = next(a for a in result["warnings"] if a["code"] == "MISSING_PAYMENT")
        assert w["severity"] == "warning"

    async def test_errors_and_warnings_are_partitioned(self) -> None:
        """errors/warnings lists are correct subsets of anomalies."""
        xml = _build_xml(total="200.00", date_str="2099-01-01")
        result = await find_invoice_anomalies(xml)
        for e in result["errors"]:
            assert e["severity"] == "error"
        for w in result["warnings"]:
            assert w["severity"] == "warning"
        all_codes = {a["code"] for a in result["anomalies"]}
        partition_codes = {a["code"] for a in result["errors"] + result["warnings"]}
        assert all_codes == partition_codes


class TestFindInvoiceAnomaliesCtx:
    """Context logging and progress notifications."""

    async def test_progress_emits_four_steps(self) -> None:
        """Happy path reports steps 1/4, 2/4, 3/4, 4/4 in order."""
        ctx = MockCtx()
        await find_invoice_anomalies(_CLEAN_XML, ctx=ctx)  # type: ignore[arg-type]
        assert ctx.progress == [(1, 4), (2, 4), (3, 4), (4, 4)]

    async def test_ctx_emits_start_and_done(self) -> None:
        """Two info log entries are emitted: start and done."""
        ctx = MockCtx()
        await find_invoice_anomalies(_CLEAN_XML, ctx=ctx)  # type: ignore[arg-type]
        assert len(ctx.infos) == 2
        assert len(ctx.errors) == 0

    async def test_no_ctx_does_not_raise(self) -> None:
        """Calling without ctx must not raise."""
        result = await find_invoice_anomalies(_CLEAN_XML, ctx=None)
        assert result["is_clean"] is True


class TestFindInvoiceAnomaliesFilePath:
    """file_path / roots-check integration."""

    async def test_file_path_within_roots(self, tmp_path: Path) -> None:
        """Providing a file_path within allowed roots reads and analyses the invoice."""
        invoice = tmp_path / "invoice.xml"
        invoice.write_text(_CLEAN_XML, encoding="utf-8")
        env_backup = os.environ.pop("FATTURAPA_ALLOWED_ROOTS", None)
        try:
            result = await find_invoice_anomalies(file_path=str(invoice))
            assert result["is_clean"] is True
        finally:
            if env_backup is not None:
                os.environ["FATTURAPA_ALLOWED_ROOTS"] = env_backup

    async def test_file_path_outside_roots_raises(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A file_path outside the allowed roots raises PermissionError."""
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        outside = tmp_path / "outside" / "inv.xml"
        outside.parent.mkdir()
        outside.write_text(_CLEAN_XML, encoding="utf-8")
        monkeypatch.setenv("FATTURAPA_ALLOWED_ROOTS", str(allowed))
        with pytest.raises(PermissionError):
            await find_invoice_anomalies(file_path=str(outside))

    async def test_neither_xml_nor_file_path_raises(self) -> None:
        """Passing neither xml_content nor file_path raises ValueError."""
        with pytest.raises(ValueError):
            await find_invoice_anomalies()
