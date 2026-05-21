"""Screen-level UI helpers."""

from __future__ import annotations

from rich.console import Console

from leap_tree_game.game.prompts import GENRES, OPENINGS, SETTINGS
from leap_tree_game.game.state import GameSetup
from leap_tree_game.ui.forms import ask_menu_choice


def ask_game_setup(*, console: Console) -> GameSetup:
    console.print("[bold]Start a new story[/bold]")
    genre = ask_menu_choice("Genre", GENRES, console=console)
    setting = ask_menu_choice("Setting", SETTINGS, console=console)
    opening = ask_menu_choice("Opening", OPENINGS, console=console)
    return GameSetup(genre=genre, setting=setting, opening=opening)
