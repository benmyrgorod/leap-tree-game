from __future__ import annotations

import pytest

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
    client = StoryClient(_settings(), agent=agent)

    response = client.generate_initial(
        GameSetup(genre="Fantasy", setting="Middle Ages", opening="Once upon a time in a distant land")
    )

    assert response.option_b == ", the hill refused him."
    assert response.story == "Once upon a time in a distant land"
    assert "Fantasy" in agent.prompts[0]


def test_story_client_malformed_output_becomes_recoverable_error() -> None:
    client = StoryClient(_settings(), agent=FakeAgent({"story": "Only one field"}))

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
    client = StoryClient(_settings(), agent=agent)
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


def _settings() -> ProviderSettings:
    return ProviderSettings(
        provider="openai",
        model="gpt-5.2",
        openai_api_key="sk-test",
    )
