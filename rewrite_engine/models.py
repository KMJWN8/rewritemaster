from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias


@dataclass(frozen=True, slots=True)
class ParsedParagraph:
    id: int
    text: str
    style: str
    can_rewrite: bool


@dataclass(frozen=True, slots=True)
class ParsedDocument:
    paragraphs: tuple[ParsedParagraph, ...]

    def rewritable(self) -> tuple[ParsedParagraph, ...]:
        """Return paragraphs eligible for rewriting, in document order."""
        return tuple(p for p in self.paragraphs if p.can_rewrite)

    def by_id(self) -> dict[int, ParsedParagraph]:
        return {p.id: p for p in self.paragraphs}

    def __len__(self) -> int:
        return len(self.paragraphs)

    def __iter__(self):
        return iter(self.paragraphs)


RewriteResults: TypeAlias = dict[int, str]
