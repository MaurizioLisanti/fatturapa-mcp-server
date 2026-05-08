"""Tests for the verify_piva_vies tool."""

import httpx
from pytest_httpx import HTTPXMock

from fatturapa_mcp.tools.vies import _VIES_URL, verify_piva_vies

_IT_URL = _VIES_URL.format(country_code="IT", vat_number="12345678901")
_DE_URL = _VIES_URL.format(country_code="DE", vat_number="123456789")


class TestVerifyPivaVies:
    # ── Happy path ──────────────────────────────────────────────────────────

    async def test_valid_vat_returns_true(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=_IT_URL,
            json={
                "isValid": True,
                "name": "ESEMPIO SRL",
                "address": "VIA ROMA 1, 00100 ROMA",
            },
        )
        result = await verify_piva_vies("IT", "12345678901")
        assert result["valid"] is True
        assert result["source"] == "vies"
        assert result["name"] == "ESEMPIO SRL"
        assert result["address"] == "VIA ROMA 1, 00100 ROMA"

    async def test_invalid_vat_returns_false(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=_IT_URL,
            json={"isValid": False, "name": "---", "address": "---"},
        )
        result = await verify_piva_vies("IT", "12345678901")
        assert result["valid"] is False
        assert result["source"] == "vies"

    async def test_undisclosed_name_returns_none(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=_IT_URL,
            json={"isValid": True, "name": "---", "address": "VIA ROMA 1"},
        )
        result = await verify_piva_vies("IT", "12345678901")
        assert result["name"] is None
        assert result["address"] == "VIA ROMA 1"

    async def test_undisclosed_address_returns_none(
        self, httpx_mock: HTTPXMock
    ) -> None:
        httpx_mock.add_response(
            url=_IT_URL,
            json={"isValid": True, "name": "ESEMPIO SRL", "address": "---"},
        )
        result = await verify_piva_vies("IT", "12345678901")
        assert result["address"] is None
        assert result["name"] == "ESEMPIO SRL"

    async def test_non_it_country(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=_DE_URL,
            json={"isValid": True, "name": "MUSTER GMBH", "address": "---"},
        )
        result = await verify_piva_vies("DE", "123456789")
        assert result["valid"] is True
        assert result["source"] == "vies"

    async def test_country_code_uppercased(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=_IT_URL,
            json={"isValid": True, "name": "---", "address": "---"},
        )
        # lowercase country code must be normalised before the request
        result = await verify_piva_vies("it", "12345678901")
        assert result["source"] == "vies"

    # ── Degraded / error paths ──────────────────────────────────────────────

    async def test_timeout_returns_unavailable(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_exception(httpx.TimeoutException("timeout"), url=_IT_URL)
        result = await verify_piva_vies("IT", "12345678901")
        assert result["valid"] is False
        assert result["source"] == "unavailable"
        assert result["name"] is None
        assert result["address"] is None

    async def test_connection_error_returns_unavailable(
        self, httpx_mock: HTTPXMock
    ) -> None:
        httpx_mock.add_exception(httpx.ConnectError("refused"), url=_IT_URL)
        result = await verify_piva_vies("IT", "12345678901")
        assert result["source"] == "unavailable"

    async def test_http_500_returns_unavailable(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(url=_IT_URL, status_code=500)
        result = await verify_piva_vies("IT", "12345678901")
        assert result["source"] == "unavailable"

    async def test_missing_is_valid_field_defaults_false(
        self, httpx_mock: HTTPXMock
    ) -> None:
        httpx_mock.add_response(
            url=_IT_URL,
            json={"name": "ESEMPIO SRL", "address": "---"},
        )
        result = await verify_piva_vies("IT", "12345678901")
        assert result["valid"] is False
        assert result["source"] == "vies"
