from __future__ import annotations

from rich.console import Console

from leap_tree_game.models.story import StoryResponse
from leap_tree_game.ui.console import render_turn_screen
from leap_tree_game.ui.forms import render_menu_screen


def test_turn_screen_renders_frame_story_and_choices() -> None:
    console = Console(record=True, force_terminal=False, width=90)

    render_turn_screen(
        StoryResponse(
            story="On a perfectly ordinary impossible day",
            option_a=", a brass cloud knocked politely.",
            option_b=", the clock ran backward.",
        ),
        active_console=console,
        subtitle="openai / gpt-5.2",
    )

    output = console.export_text()

    assert "Leap Tree" in output
    assert "Current story" in output
    assert "On a perfectly ordinary impossible day" in output
    assert "A." in output
    assert "B." in output
    assert "Choose: a, b, r, q" in output


def test_menu_screen_renders_as_framed_question() -> None:
    console = Console(record=True, force_terminal=False, width=80)

    render_menu_screen(
        "Genre",
        ["Mystery", "Other"],
        console=console,
        subtitle="setup 1/3",
    )

    output = console.export_text()

    assert "Genre" in output
    assert "Select an option" in output
    assert "Mystery" in output
    assert "Other" in output
    assert "setup 1/3" in output
