from __future__ import annotations

import pytest

import leap_tree_game.game.prompts as prompt_module
from leap_tree_game.config.settings import ProviderSettings
from leap_tree_game.game.state import GameSetup, GameState
from leap_tree_game.providers.agent import StoryClient, StoryGenerationError


class FakeResult:
    def __init__(self, output):
        self.output = output


class FakeAgent:
    def __init__(self, output):
        self.output = output
        self.prompts: list[str] = []

    def run_sync(self, prompt: str):
        self.prompts.append(prompt)
        return FakeResult(self.output)


def test_story_client_accepts_fake_agent_valid_response() -> None:
    agent = FakeAgent(
        {
            "story": "The model tried to rewrite this.",
            "option_a": ", a road introduced itself.",
            "option_b": ", the hill refused him.",
        }
    )
    client = _client(agent)

    response = client.generate_initial(
        GameSetup(genre="Fantasy", setting="Middle Ages", opening="Once upon a time in a distant land")
    )

    assert response.option_b == ", the hill refused him."
    assert response.story == "Once upon a time in a distant land"
    assert "Fantasy" in agent.prompts[0]


def test_story_client_malformed_output_becomes_recoverable_error() -> None:
    client = _client(FakeAgent({"story": "Only one field"}))

    with pytest.raises(StoryGenerationError):
        client.generate_initial(
            GameSetup(genre="Fantasy", setting="Middle Ages", opening="Once upon a time in a distant land")
        )


def test_story_client_next_prompt_includes_choice() -> None:
    agent = FakeAgent(
        {
            "story": "A new branch lowered like a ladder.",
            "option_a": "Step onto leaves",
            "option_b": "Call for help",
        }
    )
    client = _client(agent, "continue_sentence")
    state = GameState(
        setup=GameSetup(
            genre="Mystery",
            setting="Fantasy",
            opening="Shortly before reality lost control",
        )
    )
    state.append_response(
        client.generate_initial(state.setup)
    )
    choice = state.choose("A")

    response = client.generate_next(state, choice)

    assert "The player selected option A" in agent.prompts[-1]
    assert response.story == "Shortly before reality lost control Step onto leaves"


def test_story_client_capitalizes_options_after_period() -> None:
    agent = FakeAgent(
        {
            "story": "Ignored.",
            "option_a": "into the silvered grove.",
            "option_b": "toward the hidden spring.",
        }
    )
    client = _client(agent)

    response = client.generate_initial(
        GameSetup(
            genre="Mystery",
            setting="Fantasy",
            opening="A young lady mysteriously asked to follow the serpent's whisper.",
        )
    )

    assert response.option_a == "Into the silvered grove."
    assert response.option_b == "Toward the hidden spring."


def test_story_client_keeps_lowercase_fragment_when_story_does_not_end_period() -> None:
    agent = FakeAgent(
        {
            "story": "Ignored.",
            "option_a": "into the silvered grove",
            "option_b": "toward the hidden spring",
        }
    )
    client = _client(agent, "continue_sentence")

    response = client.generate_initial(
        GameSetup(
            genre="Mystery",
            setting="Fantasy",
            opening="A young lady mysteriously asked",
        )
    )

    assert response.option_a == "into the silvered grove"
    assert response.option_b == "toward the hidden spring"


def test_story_client_strips_terminal_punctuation_when_option_should_not_end_sentence() -> None:
    agent = FakeAgent(
        {
            "story": "Ignored.",
            "option_a": "into the silvered grove.",
            "option_b": "toward the hidden spring!",
        }
    )
    client = _client(agent, "continue_sentence")

    response = client.generate_initial(
        GameSetup(
            genre="Mystery",
            setting="Fantasy",
            opening="A young lady mysteriously asked",
        )
    )

    assert response.option_a == "into the silvered grove"
    assert response.option_b == "toward the hidden spring"


def test_story_client_adds_period_when_option_should_end_sentence() -> None:
    agent = FakeAgent(
        {
            "story": "Ignored.",
            "option_a": "into the silvered grove",
            "option_b": "toward the hidden spring?",
        }
    )
    client = _client(agent, "end_sentence")

    response = client.generate_initial(
        GameSetup(
            genre="Mystery",
            setting="Fantasy",
            opening="A young lady mysteriously asked",
        )
    )

    assert response.option_a == "into the silvered grove."
    assert response.option_b == "toward the hidden spring?"


def test_story_client_default_picker_alternates_sentence_endings(monkeypatch) -> None:
    monkeypatch.setattr(
        prompt_module,
        "choose_continuation_shape",
        lambda: "continue_sentence",
    )
    agent = FakeAgent(
        {
            "story": "Ignored.",
            "option_a": "into the silvered grove.",
            "option_b": "toward the hidden spring.",
        }
    )
    client = StoryClient(_settings(), agent=agent)
    setup = GameSetup(
        genre="Mystery",
        setting="Fantasy",
        opening="A young lady mysteriously asked",
    )

    first = client.generate_initial(setup)
    second = client.generate_initial(setup)

    assert first.option_a == "into the silvered grove"
    assert second.option_a == "into the silvered grove."


def _settings() -> ProviderSettings:
    return ProviderSettings(
        provider="openai",
        model="gpt-5.2",
        openai_api_key="sk-test",
    )


def _client(agent: FakeAgent, continuation_shape: str = "end_sentence") -> StoryClient:
    return StoryClient(
        _settings(),
        agent=agent,
        continuation_shape_picker=lambda: continuation_shape,
    )
