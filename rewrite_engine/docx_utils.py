from __future__ import annotations

from docx.oxml.ns import qn

EMPHASIS_TAGS = ("b", "i", "u", "strike")
_FALSE_VALUES = frozenset({"0", "false", "off"})


def run_flag(run, tag: str) -> bool:
    """Read an explicit boolean character property from a DOCX run."""
    properties = run._element.find(qn("w:rPr"))
    if properties is None:
        return False

    element = properties.find(qn(f"w:{tag}"))
    if element is None:
        return False

    value = element.get(qn("w:val"))
    return value is None or value.lower() not in _FALSE_VALUES


def run_emphasis_signature(run) -> tuple[bool, ...]:
    """Return the run's explicit bold, italic, underline and strike flags."""
    return tuple(run_flag(run, tag) for tag in EMPHASIS_TAGS)


def has_mixed_inline_formatting(paragraph) -> bool:
    """Check whether visible text runs use different emphasis settings."""
    signatures = {run_emphasis_signature(run) for run in paragraph.runs if run.text}
    return len(signatures) > 1
