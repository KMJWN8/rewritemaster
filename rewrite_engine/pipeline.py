# pipeline.py
from __future__ import annotations

import logging
from pathlib import Path

from models import ParsedDocument, ParsedParagraph
from parser import DocumentParser
from rewriter import BatchParseError, LLMClient, Rewriter
from writer import DocumentWriter

logger = logging.getLogger(__name__)

BATCH_SIZE = 8
CONTEXT_SIZE = 1  # context paragraphs on each side of the batch
MAX_SPLIT_DEPTH = 3


def rewrite_document(
    source_path: Path,
    output_path: Path,
    client: LLMClient,
) -> ParsedDocument:
    """End-to-end pipeline. Returns the ParsedDocument for inspection."""
    parsed = DocumentParser().parse(source_path)
    rewriter = Rewriter(client)

    results = _rewrite_all(parsed, rewriter)
    DocumentWriter().write(source_path, results, output_path)

    return parsed


# --------------------------------------------------------------------------- #
# Batching + retry
# --------------------------------------------------------------------------- #


def _rewrite_all(
    parsed: ParsedDocument,
    rewriter: Rewriter,
) -> dict[int, str]:
    targets = parsed.rewritable()
    if not targets:
        logger.info('No paragraphs eligible for rewriting')
        return {}

    results: dict[int, str] = {}

    for start in range(0, len(targets), BATCH_SIZE):
        batch = list(targets[start : start + BATCH_SIZE])
        end = start + len(batch)

        context_before = targets[start - 1] if start > 0 else None
        context_after = targets[end] if end < len(targets) else None

        results.update(
            _rewrite_with_split_retry(
                rewriter,
                batch,
                context_before,
                context_after,
            ),
        )

    return results


def _rewrite_with_split_retry(
    rewriter: Rewriter,
    batch: list[ParsedParagraph],
    ctx_before: ParsedParagraph | None,
    ctx_after: ParsedParagraph | None,
    depth: int = 0,
) -> dict[int, str]:
    """Retry malformed batches by splitting them into smaller batches."""
    if not batch:
        return {}

    try:
        return rewriter.rewrite_batch(
            batch,
            context_before=ctx_before,
            context_after=ctx_after,
        )
    except BatchParseError as exc:
        logger.warning(
            'Batch parsing failed: depth=%d, ids=%s, missing=%s, extra=%s',
            depth,
            [p.id for p in batch],
            exc.missing,
            exc.extra,
        )

    if len(batch) == 1 or depth >= MAX_SPLIT_DEPTH:
        logger.error(
            'Keeping original text for paragraph IDs: %s',
            [p.id for p in batch],
        )
        return {p.id: p.text for p in batch}

    mid = len(batch) // 2

    left = _rewrite_with_split_retry(
        rewriter,
        batch[:mid],
        ctx_before,
        batch[mid],
        depth + 1,
    )

    right = _rewrite_with_split_retry(
        rewriter,
        batch[mid:],
        batch[mid - 1],
        ctx_after,
        depth + 1,
    )

    return left | right


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

if __name__ == '__main__':
    import logging
    import sys

    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) != 3:
        print('usage: python pipeline.py input.docx output.docx')
        raise SystemExit(1)

    from rewrite_engine.clients.llm_polza import PolzaClient

    rewrite_document(
        Path(sys.argv[1]),
        Path(sys.argv[2]),
        PolzaClient(),
    )
