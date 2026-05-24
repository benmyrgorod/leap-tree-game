from __future__ import annotations

from rich.console import Console

from leap_tree_game import __version__
from leap_tree_game.models.story import StoryResponse
from leap_tree_game.ui.console import render_title, render_turn_screen
from leap_tree_game.ui.forms import render_menu_screen
from leap_tree_game.ui.screens import _with_other_option


def test_render_title_includes_version() -> None:
    console = Console(record=True, force_terminal=False, width=80)

    render_title(active_console=console, version=__version__)

    output = console.export_text()

    assert "Leap Tree Game" in output
    assert __version__ in output


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

    assert "Leap Tree Game" in output
    assert "Current story" in output
    assert "On a perfectly ordinary impossible day" in output
    assert "A." in output
    assert "B." in output
    assert "Choose: a (first option), b (second option), r (regenerate), s (restart), q (quit)" in output


def test_turn_screen_renders_ascii_art_before_story() -> None:
    console = Console(record=True, force_terminal=False, width=100)
    ascii_art = "/--\\\n|**|\n\\--/"

    render_turn_screen(
        StoryResponse(
            story="On a perfectly ordinary impossible day",
            option_a="into the silvered grove",
            option_b="toward the hidden spring.",
        ),
        ascii_art=ascii_art,
        active_console=console,
        subtitle="openai / gpt-5.2",
    )

    output = console.export_text()

    scene_index = output.find(ascii_art.splitlines()[0])
    story_index = output.find("Current story")
    assert scene_index != -1
    assert story_index != -1
    assert scene_index < story_index


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


def test_opening_options_append_single_other_choice() -> None:
    assert _with_other_option(
        [
            "The sheriff woke inside his own wanted poster.",
            "Other",
            "The sheriff woke inside his own wanted poster.",
            "A chapel bell rang from under the dust.",
        ]
    ) == [
        "The sheriff woke inside his own wanted poster.",
        "A chapel bell rang from under the dust.",
        "Other",
    ]
