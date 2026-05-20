"""Tests for the verify_piva_vies tool."""

import httpx
from pytest_httpx import HTTPXMock

from fatturapa_mcp.tools.vies import _VIES_URL, verify_piva_vies
from tests.conftest import MockCtx

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


class TestVerifyPivaViesCtxLogging:
    """Verify ctx log calls are emitted with correct structure."""

    async def test_valid_response_emits_start_and_done(
        self, httpx_mock: HTTPXMock
    ) -> None:
        """A successful VIES response produces two info log entries."""
        httpx_mock.add_response(
            url=_IT_URL,
            json={"isValid": True, "name": "ESEMPIO SRL", "address": "---"},
        )
        ctx = MockCtx()
        await verify_piva_vies("IT", "12345678901", ctx=ctx)  # type: ignore[arg-type]
        assert len(ctx.infos) == 2

    async def test_unavailable_emits_warning(self, httpx_mock: HTTPXMock) -> None:
        """A network error routes the done log to ctx.warning."""
        httpx_mock.add_exception(httpx.TimeoutException("timeout"), url=_IT_URL)
        ctx = MockCtx()
        await verify_piva_vies("IT", "12345678901", ctx=ctx)  # type: ignore[arg-type]
        assert len(ctx.warnings) == 1


class TestVerifyPivaViesProgress:
    """Verify progress notifications are emitted in the correct order."""

    async def test_valid_response_emits_four_steps(self, httpx_mock: HTTPXMock) -> None:
        """Happy path reports steps 1/4, 2/4, 3/4, 4/4 in order."""
        httpx_mock.add_response(
            url=_IT_URL,
            json={"isValid": True, "name": "ESEMPIO SRL", "address": "---"},
        )
        ctx = MockCtx()
        await verify_piva_vies("IT", "12345678901", ctx=ctx)  # type: ignore[arg-type]
        assert ctx.progress == [(1, 4), (2, 4), (3, 4), (4, 4)]

    async def test_network_error_emits_two_steps(self, httpx_mock: HTTPXMock) -> None:
        """Network failure stops after step 2 (pre-call steps only)."""
        httpx_mock.add_exception(httpx.TimeoutException("timeout"), url=_IT_URL)
        ctx = MockCtx()
        await verify_piva_vies("IT", "12345678901", ctx=ctx)  # type: ignore[arg-type]
        assert ctx.progress == [(1, 4), (2, 4)]

    async def test_no_ctx_does_not_raise(self, httpx_mock: HTTPXMock) -> None:
        """Calling without ctx must not raise."""
        httpx_mock.add_response(
            url=_IT_URL,
            json={"isValid": True, "name": "ESEMPIO SRL", "address": "---"},
        )
        result = await verify_piva_vies("IT", "12345678901", ctx=None)
        assert result["valid"] is True
