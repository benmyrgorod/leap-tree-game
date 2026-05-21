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
            story="The first whale appeared on the subway platform.",
            option_a="Question the conductor",
            option_b="Follow wet footprints",
        )
    )
    state.choose("B")
    state.append_response(
        StoryResponse(
            story="The footprints ended beside an unplugged payphone.",
            option_a="Dial the number",
            option_b="Smash the receiver",
        )
    )

    history = state.full_story_history()

    assert "Nobody understood why the whales suddenly" in history
    assert "The first whale appeared on the subway platform." in history
    assert "Turn 1 selected option B: Follow wet footprints" in history
    assert "The footprints ended beside an unplugged payphone." in history
