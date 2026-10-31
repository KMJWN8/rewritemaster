# rewriter.py
from __future__ import annotations

import re
from typing import Protocol

from constants import SYSTEM_PROMPT
from models import ParsedParagraph

# Backreference \1 enforces that the closing id matches the opening id.
_BLOCK_RE = re.compile(
    r"###BEGIN_(\d+)###\s*(.*?)\s*###END_\1###",
    re.DOTALL,
)


class BatchParseError(RuntimeError):
    """Raised when the model response does not match the expected format."""

    def __init__(self, missing: list[int], extra: list[int]):
        super().__init__(f"missing ids: {missing}; unexpected ids: {extra}")
        self.missing = missing
        self.extra = extra


class LLMClient(Protocol):
    """Minimal interface a batched rewriter needs from an LLM client.

    Implementations wrap a specific provider (OpenAI, YandexGPT, etc.).
    """

    def complete(self, system: str, user: str) -> str:
        """Return the raw assistant message as a string."""
        ...


class Rewriter:
    """Rewrites ONE batch of paragraphs. Knows nothing about the DOCX.

    The caller (pipeline) is responsible for:
        * choosing the batch,
        * choosing context paragraphs,
        * retrying on BatchParseError.
    """

    SYSTEM_PROMPT = SYSTEM_PROMPT

    def __init__(
        self,
        client: LLMClient,
        *,
        temperature: float = 0.3,
        max_tokens: int = 3000,
    ) -> None:
        self._client = client
        self._temperature = temperature
        self._max_tokens = max_tokens

    def rewrite_batch(
        self,
        batch: list[ParsedParagraph],
        *,
        context_before: ParsedParagraph | None = None,
        context_after: ParsedParagraph | None = None,
    ) -> dict[int, str]:
        """Rewrite one batch. Raises BatchParseError on malformed output."""
        if not batch:
            return {}

        user = self._build_user_message(batch, context_before, context_after)
        raw = self._client.complete(self.SYSTEM_PROMPT, user)
        return self._parse_response(raw, {p.id for p in batch})

    # --- internals --------------------------------------------------------

    @staticmethod
    def _build_user_message(
        batch: list[ParsedParagraph],
        context_before: ParsedParagraph | None,
        context_after: ParsedParagraph | None,
    ) -> str:
        parts: list[str] = [
            "Rewrite the TARGET paragraphs. Use the CONTEXT paragraphs ",
            "only to understand the connections between ideas; do not ",
            "rewrite them.",
            "",
        ]

        if context_before is not None:
            parts += [
                "--- CONTEXT BEFORE (do not rewrite) ---",
                f"###BEGIN_{context_before.id}###",
                context_before.text,
                f"###END_{context_before.id}###",
                "",
            ]

        parts.append("--- TARGET PARAGRAPHS (rewrite these) ---")
        for p in batch:
            parts += [
                f"###BEGIN_{p.id}###",
                p.text,
                f"###END_{p.id}###",
                "",
            ]

        if context_after is not None:
            parts += [
                "--- CONTEXT AFTER (do not rewrite) ---",
                f"###BEGIN_{context_after.id}###",
                context_after.text,
                f"###END_{context_after.id}###",
                "",
            ]

        return "\n".join(parts)

    @staticmethod
    def _parse_response(
        raw: str,
        expected_ids: set[int],
    ) -> dict[int, str]:
        found: dict[int, str] = {}
        duplicates: set[int] = set()

        for match in _BLOCK_RE.finditer(raw):
            paragraph_id = int(match.group(1))
            text = match.group(2).strip()

            if paragraph_id in found:
                duplicates.add(paragraph_id)
                continue

            found[paragraph_id] = text

        missing = sorted(expected_ids - found.keys())
        extra = sorted(found.keys() - expected_ids)

        if missing or extra or duplicates:
            raise BatchParseError(
                missing=missing,
                extra=sorted(set(extra) | duplicates),
            )

        if any(not found[paragraph_id] for paragraph_id in expected_ids):
            raise BatchParseError(
                missing=sorted(
                    paragraph_id
                    for paragraph_id in expected_ids
                    if not found[paragraph_id]
                ),
                extra=[],
            )

        # Preserve the order of requested IDs, independent of response order.
        return {paragraph_id: found[paragraph_id] for paragraph_id in expected_ids}
