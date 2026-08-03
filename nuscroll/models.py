"""Core data models."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PlannerEntry:
    module_code: str
    label: str            # e.g. "Y1S1", "Exempted", "Wishlist"
    sort_key: tuple       # ordering key across all entries


@dataclass(frozen=True)
class Review:
    author: str
    created_at: str       # ISO 8601 string from Disqus
    message: str          # plain text (HTML already stripped)
    likes: int


@dataclass
class ModuleReviews:
    module_code: str
    title: str            # "" when title unknown
    label: str
    reviews: list[Review] = field(default_factory=list)
    error: str | None = None   # non-None if the fetch failed
