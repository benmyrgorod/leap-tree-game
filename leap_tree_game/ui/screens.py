"""Screen-level UI helpers."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from rich.console import Console

from leap_tree_game.game.prompts import GENRES, OPENINGS, SETTINGS
from leap_tree_game.game.state import GameSetup
from leap_tree_game.ui.forms import OTHER_LABEL, ask_menu_choice


OpeningOptionsProvider = Callable[[str, str], Sequence[str] | None]


def ask_game_setup(
    *,
    console: Console,
    provider_summary: str | None = None,
    opening_options_provider: OpeningOptionsProvider | None = None,
) -> GameSetup | None:
    genre = ask_menu_choice(
        "Genre",
        GENRES,
        console=console,
        subtitle=_subtitle("setup 1/3", provider_summary),
    )
    setting = ask_menu_choice(
        "Setting",
        SETTINGS,
        console=console,
        subtitle=_subtitle("setup 2/3", provider_summary),
    )
    opening_options = _opening_options_for(
        genre,
        setting,
        opening_options_provider=opening_options_provider,
    )
    if opening_options is None:
        return None
    opening = ask_menu_choice(
        "Opening",
        opening_options,
        console=console,
        subtitle=_subtitle("setup 3/3", provider_summary),
    )
    return GameSetup(genre=genre, setting=setting, opening=opening)


def _opening_options_for(
    genre: str,
    setting: str,
    *,
    opening_options_provider: OpeningOptionsProvider | None,
) -> list[str] | None:
    openings = (
        opening_options_provider(genre, setting)
        if opening_options_provider is not None
        else OPENINGS
    )
    if openings is None:
        return None
    return _with_other_option(openings)


def _with_other_option(openings: Sequence[str]) -> list[str]:
    options: list[str] = []
    seen: set[str] = set()
    for opening in openings:
        stripped = opening.strip()
        normalized = stripped.lower()
        if not stripped or normalized == OTHER_LABEL.lower() or normalized in seen:
            continue
        options.append(stripped)
        seen.add(normalized)
    options.append(OTHER_LABEL)
    return options


def _subtitle(step: str, provider_summary: str | None) -> str:
    if provider_summary:
        return f"{step} | {provider_summary}"
    return step
