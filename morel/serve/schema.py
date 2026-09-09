"""Pydantic schemas for the inference API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

# Hard upper bound on a single /v1/complete request. A request that asks
# to complete N items materialises an (N, dim) zero tensor per modality
# and runs a forward pass over all of them, so the bound is what keeps a
# single attacker from forcing an OOM by sending items=range(10**7).
MAX_ITEMS_PER_REQUEST = 10_000


class Fill(BaseModel):
    """Request to complete missing modalities for a set of items.

    Attributes
    ----------
        items: Item ids to complete. Bounded by
            :data:`MAX_ITEMS_PER_REQUEST`.
        modalities: Optional subset of modality names; defaults to all.
    """

    items: list[int] = Field(
        ...,
        max_length=MAX_ITEMS_PER_REQUEST,
        description=f"Item ids to complete. Capped at {MAX_ITEMS_PER_REQUEST} per request.",
    )
    modalities: list[str] | None = Field(
        default=None,
        description="Optional subset of modality names; defaults to all.",
    )


class Done(BaseModel):
    """Response containing the completed modalities per item.

    Attributes
    ----------
        completed: Mapping from modality name to per-item vectors.
    """

    completed: dict[str, list[list[float]]] = Field(
        ..., description="Mapping from modality name to per-item vectors."
    )


class Query(BaseModel):
    """Request to score a user against the catalogue.

    Attributes
    ----------
        user: User id.
        top: Number of top items to return.
    """

    user: int = Field(..., description="User id.")
    top: int = Field(default=20, description="Number of top items to return.")


class Pick(BaseModel):
    """One (item, score) pair.

    Attributes
    ----------
        item: Item id.
        score: Predicted score.
    """

    item: int
    score: float


class List(BaseModel):
    """Response with ranked items for the requested user.

    Attributes
    ----------
        items: Ranked (item, score) pairs.
    """

    items: list[Pick]


class Health(BaseModel):
    """Health probe response.

    Attributes
    ----------
        status: Service status string.
        version: Service version string.
    """

    status: str = "ok"
    version: str


def serialize(completed: dict[str, Any]) -> dict[str, list[list[float]]]:
    """Convert torch tensors to nested Python lists for JSON serialization."""
    return {name: tensor.detach().cpu().tolist() for name, tensor in completed.items()}


__all__ = [
    "Done",
    "Fill",
    "Health",
    "List",
    "Pick",
    "Query",
    "serialize",
]
