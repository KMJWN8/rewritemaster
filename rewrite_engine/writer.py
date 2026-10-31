from __future__ import annotations

import logging
from pathlib import Path

from docx import Document
from docx.text.paragraph import Paragraph

from models import RewriteResults

logger = logging.getLogger(__name__)


class DocumentWriter:
    """Apply rewrite results to a copy of the original DOCX."""

    def write(
        self,
        source_path: Path,
        results: RewriteResults,
        output_path: Path,
    ) -> None:
        source = source_path.resolve()
        output = output_path.resolve()

        if source == output:
            raise ValueError("output_path must differ from source_path")

        if not source.is_file():
            raise FileNotFoundError(source)

        document = Document(str(source))
        paragraphs = document.paragraphs
        applied = 0

        for paragraph_id, new_text in results.items():
            if (
                not isinstance(paragraph_id, int)
                or isinstance(paragraph_id, bool)
                or not 0 <= paragraph_id < len(paragraphs)
            ):
                logger.warning(
                    "Skipping invalid paragraph id: %r",
                    paragraph_id,
                )
                continue

            if not isinstance(new_text, str) or not new_text.strip():
                logger.warning(
                    "Skipping empty or invalid rewrite for paragraph %s",
                    paragraph_id,
                )
                continue

            paragraph = paragraphs[paragraph_id]

            # A final safety check: do not alter paragraphs containing
            # complex Word elements, even if a caller supplied their IDs.
            if self._contains_unsafe_content(paragraph):
                logger.warning(
                    "Skipping paragraph %s: contains protected content",
                    paragraph_id,
                )
                continue

            self._replace_paragraph_text(paragraph, new_text)
            applied += 1

        output.parent.mkdir(parents=True, exist_ok=True)
        document.save(str(output))

        logger.info(
            "Applied %s/%s rewrites; saved to %s",
            applied,
            len(results),
            output,
        )

    @staticmethod
    def _contains_unsafe_content(paragraph) -> bool:
        # Match the parser's conservative protection policy.
        protected_tags = (
            "w:drawing",
            "w:pict",
            "w:object",
            "w:footnoteReference",
            "w:endnoteReference",
            "w:commentReference",
            "w:fldSimple",
            "w:hyperlink",
            "w:instrText",
            "w:fldChar",
            "m:oMath",
            "m:oMathPara",
        )

        return any(
            paragraph._p.find(f".//{{{namespace}}}{local_name}") is not None
            for namespace, local_name in (
                (
                    "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
                    tag.removeprefix("w:"),
                )
                if tag.startswith("w:")
                else (
                    "http://schemas.openxmlformats.org/officeDocument/2006/math",
                    tag.removeprefix("m:"),
                )
                for tag in protected_tags
            )
        )

    @staticmethod
    def _replace_paragraph_text(
        paragraph: Paragraph,
        new_text: str,
    ) -> None:
        """Replace paragraph text while retaining its paragraph style.

        Reuse the first run to preserve its character formatting.
        Remove the other runs so that old text is not left behind.
        """
        runs = paragraph.runs

        if not runs:
            paragraph.add_run(new_text)
            return

        first_run = runs[0]
        first_run.text = new_text

        for run in runs[1:]:
            run._element.getparent().remove(run._element)
