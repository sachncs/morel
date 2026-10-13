"""Property checks for safe checkpoint loading."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import torch
from hypothesis import given, settings
from hypothesis import strategies as st

from morel.core.errors import Model
from morel.train.checkpoint import load

safe_scalar = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(min_value=-10_000, max_value=10_000),
    st.floats(allow_nan=False, allow_infinity=False, width=32),
    st.text(max_size=24),
)
safe_value = st.recursive(
    safe_scalar,
    lambda children: st.one_of(
        st.lists(children, max_size=4),
        st.dictionaries(st.text(max_size=16), children, max_size=4),
    ),
    max_leaves=16,
)


class Checker:
    """Aggregated property tests for checkpoint boundaries."""

    @given(st.dictionaries(st.text(max_size=16), safe_value, max_size=8))
    @settings(max_examples=20, deadline=None)
    def malformed_payload_never_leaks_internal_errors(self, payload: dict[str, Any]) -> None:
        """Arbitrary safe-serializable payloads reject as ``Model`` or load safely."""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "fuzz.pt"
            torch.save(payload, path)
            try:
                loaded = load(path)
            except Model:
                return
            assert isinstance(loaded, dict)
