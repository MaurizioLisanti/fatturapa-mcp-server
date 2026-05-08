"""Tests for the lookup_sdi_error tool."""

import pytest

from fatturapa_mcp.tools.sdi_errors import lookup_sdi_error


class TestLookupSdiError:
    def test_known_code_returns_all_keys(self) -> None:
        result = lookup_sdi_error("00001")
        assert result["code"] == "00001"
        assert len(result["description"]) > 0
        assert len(result["category"]) > 0
        assert len(result["resolution"]) > 0

    def test_struttura_code_00001(self) -> None:
        result = lookup_sdi_error("00001")
        assert result["category"] == "STRUTTURA"

    def test_struttura_code_00002(self) -> None:
        result = lookup_sdi_error("00002")
        assert result["category"] == "STRUTTURA"

    def test_contenuto_code_00101(self) -> None:
        result = lookup_sdi_error("00101")
        assert result["category"] == "CONTENUTO"

    def test_firma_code_00200(self) -> None:
        result = lookup_sdi_error("00200")
        assert result["category"] == "FIRMA"

    def test_firma_code_00202_scaduto(self) -> None:
        result = lookup_sdi_error("00202")
        assert result["category"] == "FIRMA"
        assert "scadut" in result["description"].lower()

    def test_recapito_code_00300(self) -> None:
        result = lookup_sdi_error("00300")
        assert result["category"] == "RECAPITO"

    def test_duplicato_code_00115(self) -> None:
        result = lookup_sdi_error("00115")
        assert result["category"] == "CONTENUTO"
        assert "duplicat" in result["description"].lower()

    def test_result_code_matches_input(self) -> None:
        for code in ("00001", "00103", "00201", "00304"):
            result = lookup_sdi_error(code)
            assert result["code"] == code

    def test_unknown_code_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Unknown SDI error code"):
            lookup_sdi_error("UNKNOWN")

    def test_unknown_numeric_code_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Unknown SDI error code"):
            lookup_sdi_error("99999")

    def test_empty_string_raises_value_error(self) -> None:
        with pytest.raises(ValueError):
            lookup_sdi_error("")
