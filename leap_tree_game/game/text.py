"""Shared helpers for punctuation and continuation formatting."""

from __future__ import annotations

CONTINUATION_PREFIXES = (",", ".", ";", ":", "!", "?", ")", "]", "}")
TRAILING_PUNCTUATION = (",", ".", "!", "?", ";", ":")


def append_continuation(story: str, continuation: str) -> str:
    """Append a selected continuation with sensible spacing and punctuation rules."""

    base = story.rstrip()
    tail = continuation.strip()
    if not tail:
        raise ValueError("Continuation must not be empty.")

    if tail.lower().startswith(base.lower()):
        return tail

    if tail.startswith(CONTINUATION_PREFIXES):
        while base.endswith(TRAILING_PUNCTUATION):
            base = base[:-1].rstrip()
        return f"{base}{tail}"

    return f"{base} {tail}"
