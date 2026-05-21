from __future__ import annotations

from leap_tree_game.game.state import GameSetup, GameState
from leap_tree_game.models.story import StoryResponse


def test_game_state_preserves_complete_history() -> None:
    state = GameState(
        setup=GameSetup(
            genre="Mystery",
            setting="Modern Day",
            opening="Nobody understood why the whales suddenly",
        )
    )
    state.append_response(
        StoryResponse(
            story="Nobody understood why the whales suddenly",
            option_a="started singing below the platform.",
            option_b="dragged moonlight through town.",
        )
    )
    state.choose("B")
    state.append_response(
        StoryResponse(
            story="Nobody understood why the whales suddenly dragged moonlight through town.",
            option_a="The mayor rang a bell.",
            option_b="Children followed the glow.",
        )
    )

    history = state.full_story_history()

    assert "Nobody understood why the whales suddenly" in history
    assert "Turn 1 story before choice: Nobody understood why the whales suddenly" in history
    assert "Turn 1 selected option B continuation: dragged moonlight through town." in history
    assert "Turn 1 story after choice: Nobody understood why the whales suddenly dragged moonlight through town." in history
    assert "Turn 2 story before choice: Nobody understood why the whales suddenly dragged moonlight through town." in history


def test_current_story_appends_selected_continuation() -> None:
    state = GameState(
        setup=GameSetup(
            genre="Fantasy",
            setting="Middle Ages",
            opening="On a perfectly ordinary impossible day",
        )
    )
    state.append_response(
        StoryResponse(
            story="On a perfectly ordinary impossible day",
            option_a=", a brass cloud knocked politely.",
            option_b="the town clock ran backward.",
        )
    )
    state.choose("A")

    assert state.current_story() == "On a perfectly ordinary impossible day, a brass cloud knocked politely."


def test_game_state_replace_latest_turn() -> None:
    state = GameState(
        setup=GameSetup(
            genre="Mystery",
            setting="Modern Day",
            opening="Open field, no walls.",
        )
    )
    state.append_response(
        StoryResponse(
            story="Open field, no walls.",
            option_a="the fog rolled.",
            option_b="silence listened.",
        )
    )
    state.replace_latest_turn(
        StoryResponse(
            story="Open field, no walls.",
            option_a="a raven arrived.",
            option_b="the clock reversed.",
        )
    )

    assert state.turns[-1].option_a == "a raven arrived."
    assert state.turns[-1].option_b == "the clock reversed."


def test_game_state_latest_choice_finds_recent_choice() -> None:
    state = GameState(
        setup=GameSetup(
            genre="Mystery",
            setting="Modern Day",
            opening="Open field, no walls.",
        )
    )
    state.append_response(
        StoryResponse(
            story="Open field, no walls.",
            option_a="the fog rolled.",
            option_b="silence listened.",
        )
    )
    state.choose("A")
    state.append_response(
        StoryResponse(
            story="Open field, no walls, the fog rolled.",
            option_a="and then dawn.",
            option_b="and then dusk.",
        )
    )

    latest_choice = state.latest_choice()

    assert latest_choice is not None
    assert latest_choice.label == "A"
    assert latest_choice.text == "the fog rolled."
