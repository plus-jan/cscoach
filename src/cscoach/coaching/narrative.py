"""Render feedback items as text; enforce numeric grounding (M9.4)."""

from __future__ import annotations

import re
from collections.abc import Iterable

_NUM = re.compile(r"-?\d+(?:[.,]\d+)?")


class UngroundedNumberError(ValueError):
    """Raised when rendered text contains a number not present in the payload."""


def _norm(s: str) -> str:
    return s.replace(",", "").lstrip("-")


def assert_grounded(text: str, allowed_numbers: Iterable[float | int | str]) -> None:
    """Every number in ``text`` must come from ``allowed_numbers`` (as rendered strings).

    Use for template and LLM output alike. Round numbers and ticks must be included in the
    allowed set explicitly.
    """
    allowed = {_norm(str(a)) for a in allowed_numbers}
    found = {_norm(m) for m in _NUM.findall(text)}
    bad = sorted(found - allowed)
    if bad:
        raise UngroundedNumberError(f"ungrounded numbers in feedback: {bad}")


def render_item(item: dict[str, object]) -> str:
    raise NotImplementedError("M9.4: category-specific templates (see docs/specs/05)")
