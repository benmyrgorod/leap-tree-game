from __future__ import annotations

from leap_tree_game.game.text import append_continuation


def test_append_continuation_collapses_trailing_period_and_leading_comma() -> None:
    story = "Open field, no walls.,"
    continuation = ", the fog rolled."

    assert append_continuation(story, continuation) == "Open field, no walls, the fog rolled."
