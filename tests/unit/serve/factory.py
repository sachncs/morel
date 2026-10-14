"""Tests for serving bundle artifact validation."""

from __future__ import annotations

import numpy as np
import pytest

from morel.core.errors import Model
from morel.serve.factory import _load_mask, _validate_features


class Checker:
    """Aggregated tests for serving bundle boundaries."""

    def mask(self, tmp_path) -> None:
        """Reject unreadable, malformed, and non-finite mask artifacts."""
        corrupt = tmp_path / "corrupt.npy"
        corrupt.write_bytes(b"not a NumPy file")
        with pytest.raises(Model):
            _load_mask(corrupt)

        for value in (np.ones(3), np.asarray([[1.0, np.nan]])):
            path = tmp_path / f"mask-{value.ndim}-{np.isfinite(value).all()}.npy"
            np.save(path, value)
            with pytest.raises(Model):
                _load_mask(path)

    def features(self) -> None:
        """Reject feature arrays that could leak shape or numeric errors."""
        cases = (
            {"one_dimensional": np.ones(3)},
            {"non_finite": np.asarray([[1.0, np.inf]])},
            {"left": np.ones((2, 1)), "right": np.ones((3, 1))},
        )
        for features in cases:
            with pytest.raises(Model):
                _validate_features(features)
