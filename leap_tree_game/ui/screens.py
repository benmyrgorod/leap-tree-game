"""Screen-level UI helpers."""

from __future__ import annotations

from rich.console import Console

from leap_tree_game.game.prompts import GENRES, OPENINGS, SETTINGS
from leap_tree_game.game.state import GameSetup
from leap_tree_game.ui.forms import ask_menu_choice


def ask_game_setup(*, console: Console, provider_summary: str | None = None) -> GameSetup:
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
    opening = ask_menu_choice(
        "Opening",
        OPENINGS,
        console=console,
        subtitle=_subtitle("setup 3/3", provider_summary),
    )
    return GameSetup(genre=genre, setting=setting, opening=opening)


def _subtitle(step: str, provider_summary: str | None) -> str:
    if provider_summary:
        return f"{step} | {provider_summary}"
    return step
