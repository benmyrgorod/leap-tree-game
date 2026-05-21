from __future__ import annotations

import pytest

import leap_tree_game.game.prompts as prompt_module
from leap_tree_game.config.settings import ProviderSettings
from leap_tree_game.game.state import GameSetup, GameState
from leap_tree_game.providers.agent import StoryClient, StoryGenerationError


class FakeResult:
    def __init__(self, output, usage=None):
        self.output = output
        self.usage = usage


class FakeUsage:
    def __init__(
        self,
        *,
        requests: int = 0,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cache_write_tokens: int = 0,
        cache_read_tokens: int = 0,
    ):
        self.requests = requests
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.cache_write_tokens = cache_write_tokens
        self.cache_read_tokens = cache_read_tokens


class FakeAgent:
    def __init__(self, output, usage: FakeUsage | None = None):
        self.output = output
        self.usage = usage
        self.prompts: list[str] = []

    def run_sync(self, prompt: str):
        self.prompts.append(prompt)
        return FakeResult(self.output, usage=self.usage)


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


def test_story_client_generates_ascii_art() -> None:
    agent = FakeAgent(
        "/\\\n/--\\\n||  ||\n||  ||\n\\--/"
    )
    client = _client(agent)

    ascii_art = client.generate_ascii_art(
        "The moon hung like a coin over the harbor.",
        genre="Fantasy",
        setting="Middle Ages",
    )

    assert ascii_art == "/\\\n/--\\\n||  ||\n||  ||\n\\--/"
    assert "Fantasy" in agent.prompts[-1]
    assert "Middle Ages" in agent.prompts[-1]


def test_story_client_truncates_ascii_art_to_requested_height() -> None:
    agent = FakeAgent(
        "/\\\n|**|\n--\n|**|\n/--\\\n|**|"
    )
    client = _client(agent)

    ascii_art = client.generate_ascii_art("Any opening line", height=3)

    assert ascii_art == "/\\\n|**|\n--"


def test_story_client_rejects_story_response_for_ascii_art() -> None:
    class StoryLike:
        story = "Every child in the village started to"
        option_a = "begin dancing in the square"
        option_b = "whisper about a strange light in the woods"

    agent = FakeAgent(StoryLike())
    client = _client(agent)

    with pytest.raises(StoryGenerationError):
        client.generate_ascii_art("Every child in the village started to")


def test_story_client_rejects_prose_in_ascii_art() -> None:
    agent = FakeAgent(
        "Here is the scene:\n|\\_/|\n|o o|\n|_ _|"
    )
    client = _client(agent)

    with pytest.raises(StoryGenerationError):
        client.generate_ascii_art("A young lady mysteriously asked")


def test_story_client_preserves_ascii_leading_spaces() -> None:
    raw_art = (
        "```\n"
        "   /--\\\n"
        "  /|  |\\\n"
        " / |__| \\\n"
        " ```\n"
    )
    agent = FakeAgent(raw_art)
    client = _client(agent)

    ascii_art = client.generate_ascii_art("A young lady mysteriously asked")

    first_line = ascii_art.splitlines()[0]
    assert first_line.startswith("   /--\\")


def test_story_client_normalizes_ascii_canvas_to_requested_size() -> None:
    agent = FakeAgent(" /--\\\n/\\__/")
    client = _client(agent)

    ascii_art = client.generate_ascii_art("The moon hung like a coin over the harbor.", width=8, height=4)
    lines = ascii_art.splitlines()

    assert len(lines) == 4
    assert lines[0] == " /--\\   "
    assert lines[1] == "/\\__/   "
    assert lines[2] == "        "
    assert lines[3] == "        "


def test_story_client_tracks_token_usage_from_model_response() -> None:
    agent = FakeAgent(
        {
            "story": "The moon hung like a coin over the harbor.",
            "option_a": "into the silvered grove",
            "option_b": "toward the hidden spring.",
        },
        usage=FakeUsage(
            requests=2,
            input_tokens=8,
            output_tokens=3,
            cache_write_tokens=1,
            cache_read_tokens=2,
        ),
    )
    client = _client(agent)

    client.generate_initial(
        GameSetup(
            genre="Fantasy",
            setting="Middle Ages",
            opening="Once upon a time in a distant land",
        )
    )

    assert client.total_requests == 2
    assert client.total_input_tokens == 8
    assert client.total_output_tokens == 3
    assert client.total_cache_write_tokens == 1
    assert client.total_cache_read_tokens == 2
    assert client.total_tokens == 11
    assert "input=8" in client.token_usage_summary()
    assert "output=3" in client.token_usage_summary()
    assert "total=11" in client.token_usage_summary()


def test_story_client_translates_model_not_found_error() -> None:
    class FailingAgent:
        def run_sync(self, prompt: str):
            raise Exception(
                "status_code: 404, model_name: gpt-5.3-codex-spark, body: {'message': 'The model `gpt-5.3-codex-spark` does not exist or you do not have access to it.'}"
            )

    client = StoryClient(_settings(), agent=FailingAgent())

    with pytest.raises(StoryGenerationError) as exc_info:
        client.generate_initial(
            GameSetup(
                genre="Mystery",
                setting="Modern Day",
                opening="A young lady mysteriously asked",
            )
        )

    assert "configured model 'gpt-5.3-codex-spark' is not available" in str(exc_info.value)


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
