"""Screen-level UI helpers."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from rich.console import Console

from leap_tree_game.game.prompts import (
    GENRES,
    LANGUAGE_LEVELS,
    NORMALITY_LEVELS,
    OPENINGS,
    SETTINGS,
)
from leap_tree_game.game.state import GameSetup
from leap_tree_game.i18n import localized_options, supported_language_options, t
from leap_tree_game.ui.forms import ask_menu_choice

OpeningOptionsProvider = Callable[[str, str, str, str, str], Sequence[str] | None]


def ask_game_setup(
    *,
    console: Console,
    provider_summary: str | None = None,
    opening_options_provider: OpeningOptionsProvider | None = None,
) -> GameSetup | None:
    total_steps = 6
    language = _ask_language(console=console)
    genre_labels = _localized_option_labels(GENRES, "genres", language=language)
    genre = ask_menu_choice(
        t(language, "setup.genre_title"),
        genre_labels,
        console=console,
        language=language,
        subtitle=_subtitle(language, "setup", 2, total_steps, provider_summary),
    )
    genre = _canonicalize_option(genre, GENRES, genre_labels)
    setting_labels = _localized_option_labels(SETTINGS, "settings", language=language)
    setting = ask_menu_choice(
        t(language, "setup.setting_title"),
        setting_labels,
        console=console,
        language=language,
        subtitle=_subtitle(language, "setup", 3, total_steps, provider_summary),
    )
    setting = _canonicalize_option(setting, SETTINGS, setting_labels)
    normality_labels = _localized_option_labels(
        NORMALITY_LEVELS,
        "normality_levels",
        language=language,
    )
    normality_level = ask_menu_choice(
        t(language, "setup.normality_title"),
        normality_labels,
        console=console,
        language=language,
        subtitle=_subtitle(language, "setup", 4, total_steps, provider_summary),
    )
    normality_level = _canonicalize_option(
        normality_level,
        NORMALITY_LEVELS,
        normality_labels,
    )
    language_level_labels = _localized_option_labels(
        LANGUAGE_LEVELS,
        "language_levels",
        language=language,
    )
    language_level = ask_menu_choice(
        t(language, "setup.language_level_title"),
        language_level_labels,
        console=console,
        language=language,
        subtitle=_subtitle(language, "setup", 5, total_steps, provider_summary),
    )
    language_level = _canonicalize_option(
        language_level,
        LANGUAGE_LEVELS,
        language_level_labels,
    )
    opening_options = _opening_options_for(
        genre,
        setting,
        normality_level=normality_level,
        language_level=language_level,
        language=language,
        opening_options_provider=opening_options_provider,
    )
    if opening_options is None:
        return None
    opening = ask_menu_choice(
        t(language, "setup.opening_title"),
        opening_options,
        console=console,
        language=language,
        subtitle=_subtitle(language, "setup", 6, total_steps, provider_summary),
    )
    return GameSetup(
        genre=genre,
        setting=setting,
        opening=opening,
        language=language,
        normality_level=normality_level,
        language_level=language_level,
    )


def _opening_options_for(
    genre: str,
    setting: str,
    normality_level: str,
    language_level: str,
    *,
    opening_options_provider: OpeningOptionsProvider | None,
    language: str,
) -> list[str] | None:
    openings = (
        opening_options_provider(
            genre,
            setting,
            normality_level,
            language_level,
            language,
        )
        if opening_options_provider is not None
        else OPENINGS
    )
    if openings is None:
        return None
    return _with_other_option(openings, language=language)


def _canonicalize_option(
    selected: str,
    canonical_options: Sequence[str],
    localized_options: Sequence[str],
) -> str:
    normalized_to_canonical = {
        option.lower(): canonical
        for option, canonical in zip(localized_options, canonical_options)
    }
    canonical_lookup = {option.lower(): option for option in canonical_options}
    normalized_selected = selected.strip().lower()
    return normalized_to_canonical.get(
        normalized_selected,
        canonical_lookup.get(normalized_selected, selected.strip()),
    )


def _localized_option_labels(
    canonical_options: Sequence[str],
    option_group: str,
    *,
    language: str,
) -> list[str]:
    return localized_options(language, option_group, list(canonical_options))


def _with_other_option(
    openings: Sequence[str],
    *,
    language: str = "en",
) -> list[str]:
    options: list[str] = []
    seen: set[str] = set()
    other_label = t(language, "forms.other_label")
    for opening in openings:
        stripped = opening.strip()
        normalized = stripped.lower()
        if not stripped or normalized == other_label.lower() or normalized in seen:
            continue
        options.append(stripped)
        seen.add(normalized)
    options.append(other_label)
    return options


def _ask_language(*, console: Console) -> str:
    languages = supported_language_options()
    language_options = [label for _, label in languages]
    code_by_label = {label: code for code, label in languages}

    language_label = ask_menu_choice(
        t("en", "setup.language_title"),
        language_options,
        console=console,
        subtitle=t("en", "setup.step", step=1, total=6),
    )
    return code_by_label.get(language_label, "en")


def _subtitle(
    language: str,
    phase: str,
    step: int,
    total: int,
    provider_summary: str | None,
) -> str:
    if provider_summary:
        return f"{t(language, f'{phase}.step', step=step, total=total)} | {provider_summary}"
    return t(language, f'{phase}.step', step=step, total=total)
