"""Property checks for malformed inference requests."""

from __future__ import annotations

import asyncio

import httpx
from hypothesis import given, settings
from hypothesis import strategies as st

from morel.serve import create


async def _post(path: str, payload: dict[str, object]) -> httpx.Response:
    """Send one payload through the ASGI boundary without TestClient shims."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create()),
        base_url="http://test",
    ) as client:
        return await client.post(path, json=payload)


class Checker:
    """Aggregated property tests for the HTTP boundary."""

    @given(
        st.dictionaries(
            st.text(min_size=0, max_size=24),
            st.one_of(
                st.none(),
                st.integers(min_value=-10_000, max_value=10_000),
                st.text(max_size=32),
                st.lists(st.integers(min_value=-32, max_value=32), max_size=12),
            ),
            max_size=8,
        )
    )
    @settings(max_examples=20, deadline=None)
    def malformed_complete_payload_never_500(self, payload: dict[str, object]) -> None:
        """Arbitrary JSON objects produce validation or fail-closed responses."""
        for path in ("/v1/complete", "/v1/recommend"):
            response = asyncio.run(_post(path, payload))
            assert response.status_code in {422, 503}
            assert response.headers.get("x-request-id")
            assert response.json().get("error", {}).get("request_id")
