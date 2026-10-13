"""Property checks for configuration parsing boundaries."""

from __future__ import annotations

from typing import Any

from hypothesis import given, settings
from hypothesis import strategies as st

from morel.core.config import Config
from morel.core.errors import Cfg

json_scalar = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(min_value=-10_000, max_value=10_000),
    st.floats(allow_nan=True, allow_infinity=True, width=32),
    st.text(max_size=32),
)
json_value = st.recursive(
    json_scalar,
    lambda children: st.one_of(
        st.lists(children, max_size=5),
        st.dictionaries(st.text(max_size=24), children, max_size=5),
    ),
    max_leaves=24,
)


class Checker:
    """Aggregated property tests for configuration input."""

    @given(st.dictionaries(st.text(max_size=24), json_value, max_size=10))
    @settings(max_examples=40, deadline=None)
    def malformed_payload_never_leaks_internal_errors(self, payload: dict[str, Any]) -> None:
        """Arbitrary YAML-shaped mappings either parse or raise ``Cfg``."""
        try:
            Config.parse(payload)
        except Cfg:
            return
