from __future__ import annotations

from leap_tree_game.game.prompts import GENRES, OPENINGS, SETTINGS, build_initial_prompt, build_next_prompt
from leap_tree_game.game.state import GameSetup, GameState
from leap_tree_game.models.story import StoryResponse


def test_option_constants_include_other() -> None:
    assert "Other" in GENRES
    assert "Other" in SETTINGS
    assert "Other" in OPENINGS


def test_initial_prompt_includes_setup_and_json_contract() -> None:
    setup = GameSetup(
        genre="Adventure or Quest",
        setting="Age of Pirates and Exploration",
        opening="Three strangers accidentally brought",
    )

    prompt = build_initial_prompt(setup)

    assert "Adventure or Quest" in prompt
    assert "Age of Pirates and Exploration" in prompt
    assert "Three strangers accidentally brought" in prompt
    assert '"story"' in prompt
    assert '"option_a"' in prompt
    assert "Return the opening line unchanged" in prompt
    assert "appended directly" in prompt
    assert "about 5-7 words" in prompt


def test_next_prompt_includes_full_history_and_selected_choice() -> None:
    state = GameState(
        setup=GameSetup(
            genre="Comedy",
            setting="Wild West",
            opening="On a perfectly ordinary impossible day",
        )
    )
    state.append_response(
        StoryResponse(
            story="On a perfectly ordinary impossible day",
            option_a=", a sheriff discovered singing horses.",
            option_b=", the mayor outlawed breakfast.",
        )
    )
    choice = state.choose("A")

    prompt = build_next_prompt(state, choice)

    assert "Comedy" in prompt
    assert "Wild West" in prompt
    assert "On a perfectly ordinary impossible day, a sheriff discovered singing horses." in prompt
    assert "Turn 1 option A continuation: , a sheriff discovered singing horses." in prompt
    assert "selected option A continuation: , a sheriff discovered singing horses." in prompt
    assert "The player selected option A: , a sheriff discovered singing horses." in prompt
    assert "Current canonical story so far:" in prompt
    assert "about 5-7 words" in prompt
