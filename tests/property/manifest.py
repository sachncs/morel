"""Property checks for artifact manifest parsing."""

from __future__ import annotations

import json
from typing import Any

from hypothesis import given, settings
from hypothesis import strategies as st

from morel.core.errors import Datum
from morel.data.manifest import Manifest

json_scalar = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(min_value=-10_000, max_value=10_000),
    st.floats(allow_nan=False, allow_infinity=False, width=32),
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
    """Aggregated property tests for manifest input boundaries."""

    @given(json_value)
    @settings(max_examples=40, deadline=None)
    def malformed_payload_never_leaks_internal_errors(self, payload: Any) -> None:
        """Arbitrary JSON values parse or become a typed ``Datum`` error."""
        text = json.dumps(payload)
        try:
            parsed = Manifest.parse_json(text)
        except Datum:
            return
        assert isinstance(parsed, Manifest)
