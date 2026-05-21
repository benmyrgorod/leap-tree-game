"""Pure game logic helpers that are independent of UI and networking."""

from __future__ import annotations

from leap_tree_game.game.prompts import ContinuationShape
from leap_tree_game.game.state import StoryTurn
from leap_tree_game.models.story import StoryResponse


def continuation_shape_from_texts(option_a: str, option_b: str) -> ContinuationShape:
    """Infer whether options should end the sentence.

    A pair is considered sentence-ending only when both options terminate with
    sentence punctuation.
    """

    ends_with_punctuation = ("!", ".", "?")
    if option_a.strip().endswith(ends_with_punctuation) and option_b.strip().endswith(
        ends_with_punctuation
    ):
        return "end_sentence"
    return "continue_sentence"


def continuation_shape_for_turn(turn: StoryTurn) -> ContinuationShape:
    """Return the stored continuation shape if available, otherwise infer from options."""

    if turn.continuation_shape is not None:
        return turn.continuation_shape
    return continuation_shape_from_texts(turn.option_a, turn.option_b)


def continuation_shape_for_response(response: StoryResponse) -> ContinuationShape:
    """Infer continuation shape from generated options."""

    return continuation_shape_from_texts(response.option_a, response.option_b)


def responses_match(
    baseline_a: str,
    baseline_b: str,
    candidate_a: str,
    candidate_b: str,
) -> bool:
    """Return True when two option pairs are the same ignoring order/case.

    This keeps regeneration from accepting duplicates while remaining resilient
    to pair-order flips.
    """

    return {
        baseline_a.strip().casefold(),
        baseline_b.strip().casefold(),
    } == {
        candidate_a.strip().casefold(),
        candidate_b.strip().casefold(),
    }
