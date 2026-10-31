from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.oxml.ns import qn

from docx_utils import has_mixed_inline_formatting
from models import ParsedDocument, ParsedParagraph

PLAIN_STYLE_IDS = frozenset({"Normal", "BodyText", "TextBody"})
PLAIN_STYLE_NAMES = frozenset({"normal", "body text", "основной текст"})

UNSAFE_TAGS = tuple(
    qn(tag)
    for tag in (
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
)

BIBLIOGRAPHY_MARKERS = (
    "список использованных источников",
    "список литературы",
    "библиография",
    "references",
    "bibliography",
)


class DocumentParser:
    """Read a DOCX and identify paragraphs safe for rewriting."""

    def parse(self, path: Path) -> ParsedDocument:
        document = Document(str(path))
        parsed: list[ParsedParagraph] = []
        in_bibliography = False

        for index, paragraph in enumerate(document.paragraphs):
            text = paragraph.text
            style = paragraph.style

            style_name = (style.name if style is not None else "") or ""
            is_heading = self._is_heading(style)
            is_bibliography_heading = self._is_bibliography_heading(text)

            # Recognize the bibliography heading even if its style is
            # not named "Heading" / "Заголовок".
            if is_bibliography_heading:
                in_bibliography = True
            elif in_bibliography and is_heading:
                in_bibliography = False

            can_rewrite = (
                not in_bibliography
                and self._is_plain_style(style)
                and bool(text.strip())
                and not has_mixed_inline_formatting(paragraph)
                and not self._has_unsafe_content(paragraph)
            )

            parsed.append(
                ParsedParagraph(
                    id=index,
                    text=text,
                    style=style_name,
                    can_rewrite=can_rewrite,
                )
            )

        return ParsedDocument(paragraphs=tuple(parsed))

    @staticmethod
    def _is_plain_style(style) -> bool:
        if style is None:
            return False

        style_id = (style.style_id or "").strip()
        style_name = (style.name or "").strip().casefold()

        return style_id in PLAIN_STYLE_IDS or style_name in PLAIN_STYLE_NAMES

    @staticmethod
    def _is_heading(style) -> bool:
        if style is None:
            return False

        style_id = (style.style_id or "").casefold()
        style_name = (style.name or "").casefold()

        return (
            style_id.startswith("heading")
            or style_name.startswith("heading")
            or "заголовок" in style_name
        )

    @staticmethod
    def _is_bibliography_heading(text: str) -> bool:
        normalized = " ".join(text.casefold().split())
        return bool(normalized) and any(
            marker in normalized for marker in BIBLIOGRAPHY_MARKERS
        )

    @staticmethod
    def _has_unsafe_content(paragraph) -> bool:
        element = paragraph._p

        # Do not replace text in paragraphs containing Word elements
        # that a plain-text rewrite cannot safely reconstruct.
        return any(element.find(f".//{tag}") is not None for tag in UNSAFE_TAGS)
