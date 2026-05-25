from __future__ import annotations

from io import StringIO

import pytest
from rich.console import Console

from leap_tree_game.config.settings import ProviderSettings
from leap_tree_game.game.engine import GameEngine
from leap_tree_game.game.state import GameSetup, GameState
from leap_tree_game.models.story import StoryResponse


def test_turn_choice_logs_user_decision(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[tuple[str, dict[str, object]]] = []
    def capture_event(name: str, **fields: object) -> None:
        events.append((name, fields))

    def generate_next(*_args, **_kwargs) -> StoryResponse:
        return StoryResponse(
            story="A fresh branch",
            option_a="left",
            option_b="right",
        )

    engine = GameEngine(
        ProviderSettings(provider="openai", model="gpt-5.2", openai_api_key="sk-test"),
        console=Console(file=StringIO(), force_terminal=False),
    )
    state = GameState(
        setup=GameSetup(genre="Mystery", setting="Modern Day", opening="An old bell stopped."),
    )
    state.append_response(
        StoryResponse(
            story="An old bell stopped.",
            option_a="open the door",
            option_b="stay silent",
        )
    )

    monkeypatch.setattr("leap_tree_game.game.engine.logfire_event", capture_event)
    monkeypatch.setattr(engine, "_generate_next_turn_with_retry", generate_next)
    monkeypatch.setattr(engine, "_render_turn", lambda *args, **kwargs: None)

    action = engine._handle_turn_command(state=state, command="a")

    assert action == "continue"
    assert ("user.decision", {"phase": "turn_choice", "command": "a", "turn": 1, "choice_label": "A"}) in events


def test_turn_control_command_logs_user_decision(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[tuple[str, dict[str, object]]] = []
    def capture_event(name: str, **fields: object) -> None:
        events.append((name, fields))

    engine = GameEngine(
        ProviderSettings(provider="openai", model="gpt-5.2", openai_api_key="sk-test"),
        console=Console(file=StringIO(), force_terminal=False),
    )
    state = GameState(
        setup=GameSetup(genre="Mystery", setting="Modern Day", opening="An old bell stopped."),
    )
    state.append_response(
        StoryResponse(
            story="An old bell stopped.",
            option_a="open the door",
            option_b="stay silent",
        )
    )

    monkeypatch.setattr("leap_tree_game.game.engine.logfire_event", capture_event)
    monkeypatch.setattr(engine, "_show_full_story", lambda *_args, **_kwargs: "continue")

    action = engine._handle_turn_command(state=state, command="m")

    assert action == "continue"
    assert (
        "user.decision",
        {"phase": "turn", "command": "m", "turn": 1},
    ) in events


def test_storybook_command_logs_user_decision(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[tuple[str, dict[str, object]]] = []
    def capture_event(name: str, **fields: object) -> None:
        events.append((name, fields))

    engine = GameEngine(
        ProviderSettings(provider="openai", model="gpt-5.2", openai_api_key="sk-test"),
        console=Console(file=StringIO(), force_terminal=False),
    )
    state = GameState(
        setup=GameSetup(genre="Mystery", setting="Modern Day", opening="An old bell stopped."),
    )
    state.append_response(
        StoryResponse(
            story="An old bell stopped.",
            option_a="open the door",
            option_b="stay silent",
        )
    )
    state.append_response(
        StoryResponse(
            story="A fresh branch.",
            option_a="a",
            option_b="b",
        )
    )

    monkeypatch.setattr("leap_tree_game.game.engine.logfire_event", capture_event)
    monkeypatch.setattr(
        engine,
        "_generate_storybook_with_retry",
        lambda *args, **kwargs: "A fully expanded story.",
    )

    action, _, _, _ = engine._handle_storybook_command(
        state=state,
        command="r",
        language="en",
        source_story=state.current_story(),
        current_story="full story",
    )

    assert action == "continue"
    assert (
        "user.decision",
        {"phase": "storybook", "command": "r", "turn": 2},
    ) in events
