"""Prompt templates and selectable game setup options."""

from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from leap_tree_game.game.state import Choice, GameSetup, GameState

ContinuationShape = Literal["continue_sentence", "end_sentence"]
ContinuationStart = Literal["start_new_sentence", "continue_previous_sentence"]
CONTINUATION_SHAPES: tuple[ContinuationShape, ContinuationShape] = (
    "continue_sentence",
    "end_sentence",
)

GENRES = [
    "Zero to Hero",
    "Chosen One",
    "Adventure or Quest",
    "Revenge Story",
    "Comedy",
    "Tragedy",
    "Love",
    "Mystery",
    "Other",
]

SETTINGS = [
    "Prehistoric",
    "Biblical Paradise",
    "Ancient Civilizations",
    "Classical Antiquity (Israel/Greece/Rome)",
    "Middle Ages",
    "Age of Pirates and Exploration",
    "Wild West",
    "Modern Day",
    "Post-Apocalyptic",
    "Sci Fi Paradise",
    "Fantasy",
    "Superheroes",
    "Other",
]

OPENINGS = [
    "On a perfectly ordinary impossible day",
    "Shortly before reality lost control",
    "Once upon a time in a distant land",
    "Three strangers accidentally brought",
    "Every child in the village started to",
    "Someone stole the sun and replaced it with",
    "A young lady mysteriously asked",
    "Nobody understood why the whales suddenly",
    "Other",
]

PROJECT_ROOT = Path(__file__).resolve().parents[3]
PROMPT_DIR = PROJECT_ROOT / "prompts"
CONTINUATION_SHAPE_INSTRUCTIONS: dict[ContinuationShape, str] = {
    "continue_sentence": (
        "For this turn, each option should not end the sentence."
    ),
    "end_sentence": (
        "For this turn, each option should be the end of the sentence."
    ),
}
CONTINUATION_START_INSTRUCTIONS: dict[ContinuationStart, str] = {
    "start_new_sentence": (
        'Because "story" already ends a sentence, each option should start a new sentence.'
    ),
    "continue_previous_sentence": (
        'Because "story" does not end a sentence, each option should continue the previous sentence.'
    ),
}


def build_initial_prompt(
    setup: GameSetup,
    *,
    continuation_shape: ContinuationShape | None = None,
) -> str:
    template = _load_template("initial.md")
    return _replace_placeholders(
        template,
        genre=setup.genre,
        setting=setup.setting,
        opening=setup.opening,
        continuation_start_instruction=_continuation_start_instruction(setup.opening),
        continuation_shape_instruction=_continuation_shape_instruction(continuation_shape),
    )


def build_next_prompt(
    state: GameState,
    choice: Choice,
    *,
    continuation_shape: ContinuationShape | None = None,
) -> str:
    template = _load_template("next.md")
    current_story = state.current_story()
    return _replace_placeholders(
        template,
        genre=state.setup.genre,
        setting=state.setup.setting,
        opening=state.setup.opening,
        history=state.full_story_history(),
        current_story=current_story,
        choice_label=choice.label,
        choice_text=choice.text,
        continuation_start_instruction=_continuation_start_instruction(current_story),
        continuation_shape_instruction=_continuation_shape_instruction(continuation_shape),
    )


def _load_template(name: str) -> str:
    path = PROMPT_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Prompt template not found: {path}")
    return path.read_text().strip()


def _replace_placeholders(template: str, **values: str) -> str:
    formatted = template
    for key, value in values.items():
        formatted = formatted.replace("{" + key + "}", value)
    return formatted


def _continuation_shape_instruction(shape: ContinuationShape | None) -> str:
    selected_shape = shape or choose_continuation_shape()
    return CONTINUATION_SHAPE_INSTRUCTIONS[selected_shape]


def choose_continuation_shape() -> ContinuationShape:
    return random.choice(CONTINUATION_SHAPES)


@dataclass
class BalancedContinuationShapePicker:
    """Choose the first shape randomly, then alternate for a visible 50/50 split."""

    next_shape: ContinuationShape | None = None

    def __call__(self) -> ContinuationShape:
        shape = self.next_shape or choose_continuation_shape()
        self.next_shape = opposite_continuation_shape(shape)
        return shape


def opposite_continuation_shape(shape: ContinuationShape) -> ContinuationShape:
    if shape == "continue_sentence":
        return "end_sentence"
    return "continue_sentence"


def sentence_has_ended(text: str) -> bool:
    return text.rstrip().endswith((".", "!", "?"))


def _continuation_start_instruction(story: str) -> str:
    if sentence_has_ended(story):
        return CONTINUATION_START_INSTRUCTIONS["start_new_sentence"]
    return CONTINUATION_START_INSTRUCTIONS["continue_previous_sentence"]
