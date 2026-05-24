"""Internationalization helpers and locale metadata."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

DEFAULT_LANGUAGE = "en"

SUPPORTED_LANGUAGES: tuple[str, ...] = (
    "en",
    "es",
    "fr",
    "de",
    "it",
    "pt",
    "ru",
    "ja",
    "ko",
    "zh",
)

I18N_DIR = Path(__file__).resolve().parent / "translations"


def normalize_language(language: str) -> str:
    """Return a supported language code, defaulting to English."""

    if language in SUPPORTED_LANGUAGES:
        return language
    return DEFAULT_LANGUAGE


def supported_language_options() -> list[tuple[str, str]]:
    """Return display labels for each supported language in the locale language."""

    return [
        (language, t(language, "language.menu_label"))
        for language in SUPPORTED_LANGUAGES
    ]


def localized_options(
    language: str,
    option_group: str,
    fallback: list[str],
) -> list[str]:
    """Return translated option labels for a specific group.

    Falls back to the provided fallback list if localization is missing or
    malformed.
    """

    values = _get_key(_load_language(language), f"options.{option_group}")
    if not isinstance(values, list) or len(values) != len(fallback):
        return list(fallback)
    for value in values:
        if not isinstance(value, str):
            return list(fallback)
    return [str(value).strip() for value in values]


def language_display_name(language: str) -> str:
    """Return the language label intended for prompt instructions."""

    return t(language, "language.prompt_name")


def t(language: str, key: str, **params: Any) -> str:
    """Translate a dotted-keyed UI string using the requested language."""

    resolved = _get_key(_load_language(language), key)
    if resolved is None and language != DEFAULT_LANGUAGE:
        resolved = _get_key(_load_language(DEFAULT_LANGUAGE), key)
    if not isinstance(resolved, str):
        return key
    if params:
        return resolved.format(**params)
    return resolved


@lru_cache(maxsize=None)
def _load_language(language: str) -> dict[str, Any]:
    path = I18N_DIR / f"{normalize_language(language)}.json"
    if not path.exists():
        fallback = I18N_DIR / f"{DEFAULT_LANGUAGE}.json"
        return _load_language_data(fallback)
    return _load_language_data(path)


def _load_language_data(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def _get_key(data: dict[str, Any], key: str) -> Any:
    current: Any = data
    for part in key.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current
