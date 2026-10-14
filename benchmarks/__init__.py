"""Benchmarks for morel.

Run with::

    pytest benchmarks/ -v --benchmark-only --benchmark-min-rounds=20

The 100k forward benchmark is opt-in because it is intended for deliberate
capacity characterization rather than the bounded default audit::

    MOREL_ENABLE_LARGE_BENCHMARKS=1 pytest benchmarks/forward.py -v \
        --benchmark-only --benchmark-min-rounds=3
"""

__all__ = []
