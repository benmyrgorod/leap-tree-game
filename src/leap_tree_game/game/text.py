"""Shared helpers for punctuation and continuation formatting."""

from __future__ import annotations

SENTENCE_END_MARKERS = (".", "!", "?")
CONTINUATION_PREFIXES = (",", ".", ";", ":", "!", "?", ")", "]", "}")


def sentence_has_ended(text: str) -> bool:
    """Return True when `text` ends with sentence-ending punctuation."""

    return text.rstrip().endswith(SENTENCE_END_MARKERS)


def append_continuation(story: str, continuation: str) -> str:
    """Append a selected continuation with sensible spacing and punctuation rules."""

    base = story.rstrip()
    tail = continuation.strip()
    if not tail:
        raise ValueError("Continuation must not be empty.")

    if tail.lower().startswith(base.lower()):
        return tail

    if tail.startswith(CONTINUATION_PREFIXES):
        return f"{base}{tail}"

    return f"{base} {tail}"


def capitalize_continuation_if_needed(story: str, continuation: str) -> str:
    """Uppercase the first alphabetic character when `story` ended a sentence."""

    if not sentence_has_ended(story):
        return continuation

    for index, char in enumerate(continuation):
        if char.isalpha():
            return continuation[:index] + char.upper() + continuation[index + 1 :]

    return continuation


def strip_terminal_punctuation(option: str) -> str:
    """Remove terminal `.`, `!`, and `?` markers while preserving trailing spaces."""

    trailing_whitespace = option[len(option.rstrip()) :]
    stripped = option.rstrip()
    while stripped.endswith(SENTENCE_END_MARKERS):
        stripped = stripped[:-1].rstrip()
    return f"{stripped}{trailing_whitespace}"


def ensure_terminal_punctuation(option: str) -> str:
    """Ensure a terminal `.`, `!`, or `?` marker is present."""

    stripped = option.rstrip()
    if not stripped or stripped.endswith(SENTENCE_END_MARKERS):
        return option

    trailing_whitespace = option[len(stripped) :]
    return f"{stripped}.{trailing_whitespace}"
