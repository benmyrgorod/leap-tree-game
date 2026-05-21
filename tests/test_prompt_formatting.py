from __future__ import annotations

import leap_tree_game.game.prompts as prompt_module
from leap_tree_game.game.prompts import (
    BalancedContinuationShapePicker,
    GENRES,
    OPENINGS,
    SETTINGS,
    build_initial_prompt,
    build_ascii_art_prompt,
    build_next_prompt,
    sentence_has_ended,
)
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

    prompt = build_initial_prompt(setup, continuation_shape="continue_sentence")

    assert "Adventure or Quest" in prompt
    assert "Age of Pirates and Exploration" in prompt
    assert "Three strangers accidentally brought" in prompt
    assert '"story"' in prompt
    assert '"option_a"' in prompt
    assert "Return the opening line unchanged" in prompt
    assert "appended directly" in prompt
    assert "3-7 words" in prompt
    assert "should continue the previous sentence" in prompt
    assert "should start a new sentence" not in prompt
    assert "should not end the sentence" in prompt
    assert "should be the end of the sentence" not in prompt


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

    prompt = build_next_prompt(state, choice, continuation_shape="end_sentence")

    assert "Comedy" in prompt
    assert "Wild West" in prompt
    assert "On a perfectly ordinary impossible day, a sheriff discovered singing horses." in prompt
    assert "Turn 1 option A continuation: , a sheriff discovered singing horses." in prompt
    assert "selected option A continuation: , a sheriff discovered singing horses." in prompt
    assert "The player selected option A: , a sheriff discovered singing horses." in prompt
    assert "Current canonical story so far:" in prompt
    assert "3-7 words" in prompt
    assert "should start a new sentence" in prompt
    assert "should continue the previous sentence" not in prompt
    assert "should be the end of the sentence" in prompt
    assert "should not end the sentence" not in prompt


def test_prompt_builder_randomly_selects_one_continuation_shape(monkeypatch) -> None:
    seen_options = []

    def fake_choice(options):
        seen_options.append(tuple(options))
        return "end_sentence"

    monkeypatch.setattr(prompt_module.random, "choice", fake_choice)
    setup = GameSetup(
        genre="Mystery",
        setting="Modern Day",
        opening="Someone stole the sun and replaced it with",
    )

    prompt = build_initial_prompt(setup)

    assert seen_options == [("continue_sentence", "end_sentence")]
    assert "{continuation_shape_instruction}" not in prompt
    assert "{continuation_start_instruction}" not in prompt
    assert "should be the end of the sentence" in prompt


def test_balanced_continuation_shape_picker_randomizes_then_alternates(monkeypatch) -> None:
    monkeypatch.setattr(
        prompt_module,
        "choose_continuation_shape",
        lambda: "continue_sentence",
    )
    picker = BalancedContinuationShapePicker()

    assert [picker(), picker(), picker(), picker()] == [
        "continue_sentence",
        "end_sentence",
        "continue_sentence",
        "end_sentence",
    ]


def test_initial_prompt_instructs_new_sentence_when_opening_ended() -> None:
    setup = GameSetup(
        genre="Mystery",
        setting="Modern Day",
        opening="The sun vanished.",
    )

    prompt = build_initial_prompt(setup, continuation_shape="continue_sentence")

    assert "should start a new sentence" in prompt
    assert "should continue the previous sentence" not in prompt


def test_sentence_has_ended_detects_common_sentence_punctuation() -> None:
    assert sentence_has_ended("The sun vanished.")
    assert sentence_has_ended("The sun vanished!")
    assert sentence_has_ended("The sun vanished?")
    assert not sentence_has_ended("The sun vanished")


def test_initial_prompt_includes_regeneration_avoidance_instruction() -> None:
    setup = GameSetup(
        genre="Mystery",
        setting="Modern Day",
        opening="A young lady mysteriously asked",
    )

    prompt = build_initial_prompt(
        setup,
        continuation_shape="continue_sentence",
        avoid_continuations=("the fox listened.", "the moon smiled."),
    )

    assert (
        'For this regeneration, avoid repeating the exact option text from the previous turn. '
        '"the fox listened." and "the moon smiled." should both be avoided.'
    ) in prompt


def test_next_prompt_includes_regeneration_avoidance_instruction() -> None:
    state = GameState(
        setup=GameSetup(
            genre="Mystery",
            setting="Modern Day",
            opening="A young lady mysteriously asked",
        )
    )
    state.append_response(
        StoryResponse(
            story="A young lady mysteriously asked",
            option_a="the fox listened.",
            option_b="the moon smiled.",
        )
    )
    choice = state.choose("A")
    state.append_response(
        StoryResponse(
            story="A young lady mysteriously asked the fox listened.",
            option_a="a bell rang.",
            option_b="water turned silver.",
        )
    )

    prompt = build_next_prompt(
        state,
        choice,
        continuation_shape="end_sentence",
        avoid_continuations=("the fox listened.", "the moon smiled."),
    )

    assert (
        'For this regeneration, avoid repeating the exact option text from the previous turn. '
        '"the fox listened." and "the moon smiled." should both be avoided.'
    ) in prompt


def test_ascii_prompt_includes_story_and_width() -> None:
    prompt = build_ascii_art_prompt("A crow circled the chapel bell.", width=72, height=14)

    assert "Current story context:" in prompt
    assert "Last complete sentence to illustrate:" in prompt
    assert "A crow circled the chapel bell." in prompt
    assert "72" in prompt
    assert "14" in prompt
    assert "no prose, no story text, and no labels" in prompt
    assert "exactly 14 lines" in prompt
    assert "exactly 72 characters" in prompt
    assert "Return only the ASCII image." in prompt


def test_ascii_prompt_focuses_on_last_sentence() -> None:
    prompt = build_ascii_art_prompt(
        "On a perfectly ordinary impossible day, the wind changed direction. "
        "A raven perched on the chapel bell.",
        width=40,
        height=12,
    )

    assert "A raven perched on the chapel bell." in prompt
    assert "On a perfectly ordinary impossible day, the wind changed direction." in prompt
    assert (
        "Use this last complete sentence to define the immediate scene composition."
        in prompt
    )
    assert "Keep continuity consistent with the full story context." in prompt
