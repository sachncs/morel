"""Typed exception hierarchy for morel.

Every error raised by the library is a `Error`. Specializations live in
submodules and re-export here. The base class itself ends in `Error`
(see Rule A); subclasses are named after the domain concept (see
Rule D single-word naming) rather than redundantly appending `Error`.
"""

from __future__ import annotations


class Error(Exception):
    """Base class for every exception raised by morel.

    Attributes
    ----------
        args: Inherited from Exception.
    """


class Datum(Error):  # noqa: N818  # Rule D: single-word class name (domain concept).
    """Data acquisition, validation, or loading failures.

    Attributes
    ----------
        args: Inherited from Exception.
    """


class Cfg(Error):  # noqa: N818  # Rule D: single-word class name (domain concept).
    """Invalid or inconsistent configuration.

    Attributes
    ----------
        args: Inherited from Exception.
    """


class Model(Error):  # noqa: N818  # Rule D: single-word class name (domain concept).
    """Model construction, forward, or parameter validation failures.

    Attributes
    ----------
        args: Inherited from Exception.
    """


class Net(Error):  # noqa: N818  # Rule D: single-word class name (domain concept).
    """Graph construction, invariant violation, or retrieval failures.

    Attributes
    ----------
        args: Inherited from Exception.
    """


class Train(Error):  # noqa: N818  # Rule D: single-word class name (domain concept).
    """Training loop failures (NaN loss, missing checkpoint, etc.).

    Attributes
    ----------
        args: Inherited from Exception.
    """


class Rate(Error):  # noqa: N818  # Rule D: single-word class name (domain concept).
    """Evaluation failures (empty score matrix, etc.).

    Attributes
    ----------
        args: Inherited from Exception.
    """


class Shape(Error):  # noqa: N818  # Rule D: single-word class name (domain concept).
    """Tensor shape mismatch.

    Attributes
    ----------
        args: Inherited from Exception.
    """


class Determinism(Error):  # noqa: N818  # Rule D: single-word class name (domain concept).
    """Reproducibility invariant violated.

    Attributes
    ----------
        args: Inherited from Exception.
    """


__all__ = [
    "Cfg",
    "Datum",
    "Determinism",
    "Error",
    "Model",
    "Net",
    "Rate",
    "Shape",
    "Train",
]
