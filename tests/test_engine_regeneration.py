from __future__ import annotations

from collections.abc import Sequence
from io import StringIO

from rich.console import Console

from leap_tree_game.config.settings import ProviderSettings
from leap_tree_game.game.engine import GameEngine
from leap_tree_game.game.state import GameSetup, GameState
from leap_tree_game.models.story import StoryResponse


class FakeStoryClient:
    def __init__(self, next_responses: Sequence[StoryResponse]) -> None:
        self.next_responses = list(next_responses)
        self.initial_calls: list[
            tuple[GameSetup, tuple[str, str] | None, str | None]
        ] = []
        self.next_calls: list[tuple[str, tuple[str, str] | None, str | None]] = []

    def generate_initial(
        self,
        setup: GameSetup,
        *,
        avoid_continuations: tuple[str, str] | None = None,
        continuation_shape=None,
    ) -> StoryResponse:
        self.initial_calls.append((setup, avoid_continuations, continuation_shape))
        return self._pop_response()

    def generate_next(
        self,
        state: GameState,
        choice,
        *,
        avoid_continuations: tuple[str, str] | None = None,
        continuation_shape=None,
    ) -> StoryResponse:
        self.next_calls.append((state.current_story(), avoid_continuations, continuation_shape))
        return self._pop_response()

    def _pop_response(self) -> StoryResponse:
        response = self.next_responses.pop(0)
        return response


def test_regenerate_turn_requests_diverse_options_from_story_client() -> None:
    state = _state_after_current_turn(
        StoryResponse(
            story="On a perfectly ordinary impossible day",
            option_a="into the silvered grove",
            option_b="toward the hidden spring.",
        )
    )
    duplicate = StoryResponse(
        story="On a perfectly ordinary impossible day",
        option_a="into the silvered grove",
        option_b="toward the hidden spring.",
    )
    replacement = StoryResponse(
        story="On a perfectly ordinary impossible day",
        option_a="under a black sky",
        option_b="before dawn.",
    )
    client = FakeStoryClient([duplicate, duplicate, replacement])
    engine = GameEngine(
        ProviderSettings(provider="openai", model="gpt-5.2", openai_api_key="sk-test"),
        story_client=client,
        console=Console(file=StringIO(), force_terminal=False),
    )

    response = engine._generate_regenerated_turn_with_retry(state)

    assert response.option_a == "under a black sky"
    assert response.option_b == "before dawn."
    assert len(client.next_calls) == 3
    assert client.next_calls[0][1:] == (
        ("into the silvered grove", "toward the hidden spring."),
        "continue_sentence",
    )


def test_regenerate_turn_with_no_choice_calls_generate_initial_and_avoids_previous_options() -> None:
    state = GameState(
        setup=GameSetup(
            genre="Mystery",
            setting="Modern Day",
            opening="On a perfectly ordinary impossible day",
        )
    )
    state.append_response(
        StoryResponse(
            story="On a perfectly ordinary impossible day",
            option_a="into the silvered grove",
            option_b="toward the hidden spring.",
        )
    )

    replacement = StoryResponse(
        story="On a perfectly ordinary impossible day",
        option_a="under a black sky",
        option_b="before dawn.",
    )
    client = FakeStoryClient([replacement])
    engine = GameEngine(
        ProviderSettings(provider="openai", model="gpt-5.2", openai_api_key="sk-test"),
        story_client=client,
        console=Console(file=StringIO(), force_terminal=False),
    )

    response = engine._generate_regenerated_turn_with_retry(state)

    assert response.option_a == "under a black sky"
    assert client.initial_calls == [
        (
            state.setup,
            ("into the silvered grove", "toward the hidden spring."),
            "continue_sentence",
        )
    ]


def test_regenerate_turn_preserves_previous_continuation_shape() -> None:
    state = GameState(
        setup=GameSetup(
            genre="Mystery",
            setting="Modern Day",
            opening="On a perfectly ordinary impossible day",
        )
    )
    state.append_response(
        StoryResponse(
            story="On a perfectly ordinary impossible day",
            option_a="into the silvered grove",
            option_b="toward the hidden spring.",
        ),
        continuation_shape="end_sentence",
    )
    state.choose("A")
    state.append_response(
        StoryResponse(
            story="On a perfectly ordinary impossible day into the silvered grove",
            option_a="before dawn",
            option_b="under a black sky.",
        ),
        continuation_shape="continue_sentence",
    )

    replacement = StoryResponse(
        story="On a perfectly ordinary impossible day into the silvered grove",
        option_a="under a black sky",
        option_b="before dawn.",
    )
    client = FakeStoryClient([replacement])
    engine = GameEngine(
        ProviderSettings(provider="openai", model="gpt-5.2", openai_api_key="sk-test"),
        story_client=client,
        console=Console(file=StringIO(), force_terminal=False),
    )

    engine._generate_regenerated_turn_with_retry(state)

    assert client.next_calls[0][2] == "continue_sentence"


def test_art_height_is_calculated_from_remaining_terminal_space() -> None:
    response = StoryResponse(
        story="On a perfectly ordinary impossible day",
        option_a="into the silvered grove",
        option_b="toward the hidden spring.",
    )
    engine = GameEngine(
        ProviderSettings(provider="openai", model="gpt-5.2", openai_api_key="sk-test"),
        console=Console(file=StringIO(), force_terminal=False, width=80, height=30),
    )

    art_height = engine._art_height(response)
    expected_height = max(
        3,
        30 - engine._estimated_non_art_line_count(response, engine._art_width()) - 4,
    )

    assert art_height == expected_height


def test_turn_status_includes_turn_and_token_usage() -> None:
    engine = GameEngine(
        ProviderSettings(provider="openai", model="gpt-5.2", openai_api_key="sk-test"),
        console=Console(file=StringIO(), force_terminal=False),
    )
    engine.story_client.total_input_tokens = 13
    engine.story_client.total_output_tokens = 6

    assert (
        engine._turn_status(4)
        == "turn 4 | openai / gpt-5.2 | tokens used: 19"
    )


def _state_after_current_turn(turn: StoryResponse) -> GameState:
    state = GameState(
        setup=GameSetup(
            genre="Mystery",
            setting="Modern Day",
            opening="On a perfectly ordinary impossible day",
        )
    )
    state.append_response(
        StoryResponse(
            story="On a perfectly ordinary impossible day",
            option_a="the wind answered",
            option_b="the bells listened.",
        )
    )
    state.choose("A")
    state.append_response(turn)
    return state
