"""Prompt templates and selectable game setup options."""

from __future__ import annotations

import random
import re
from functools import lru_cache
from pathlib import Path

from leap_tree_game.game.state import Choice, GameSetup, GameState
from leap_tree_game.i18n import language_display_name, normalize_language

GENRES = [
    "Zero to Hero",
    "Chosen One",
    "Adventure or Quest",
    "Revenge Story",
    "Comedy",
    "Tragedy",
    "Love",
    "Mystery",
    "Satire",
    "Thriller",
    "Crime",
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
    "Cyberpunk",
    "Steampunk",
    "Victorian Era",
    "Feudal Japan",
    "Renaissance Europe",
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
    "A bell rang in the city center",
    "Other",
]

NORMALITY_LEVELS = [
    "Highly realistic",
    "Mostly realistic",
    "Balanced",
    "Unpredictable",
    "Highly unpredictable",
]

LANGUAGE_LEVELS = [
    "Conversational",
    "Literary",
    "Geeky",
    "Poetic",
    "Cinematic",
]

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROMPT_DIR = PROJECT_ROOT / "prompts"


def build_initial_prompt(
    setup: GameSetup,
    *,
    avoid_continuations: tuple[str, str] | None = None,
    language: str | None = None,
) -> str:
    language_code = normalize_language(language or setup.language)
    return _build_prompt(
        "initial.md",
        language=language_code,
        genre=setup.genre,
        setting=setup.setting,
        opening=setup.opening,
        normality_level=setup.normality_level,
        language_level=setup.language_level,
        regeneration_avoidance_instruction=_regeneration_avoidance_instruction(
            avoid_continuations
        ),
    )


def build_next_prompt(
    state: GameState,
    choice: Choice,
    *,
    avoid_continuations: tuple[str, str] | None = None,
    language: str | None = None,
) -> str:
    current_story = state.current_story()
    language_code = normalize_language(language or state.setup.language)
    return _build_prompt(
        "next.md",
        language=language_code,
        genre=state.setup.genre,
        setting=state.setup.setting,
        opening=state.setup.opening,
        normality_level=state.setup.normality_level,
        language_level=state.setup.language_level,
        history=state.full_story_history(),
        current_story=current_story,
        choice_label=choice.label,
        choice_text=choice.text,
        regeneration_avoidance_instruction=_regeneration_avoidance_instruction(
            avoid_continuations
        ),
    )


def build_ascii_art_prompt(
    story: str,
    *,
    genre: str | None = None,
    setting: str | None = None,
    language: str | None = None,
    width: int | None = None,
    height: int | None = None,
) -> str:
    target_width = str(width or 80)
    target_height = str(height or 12)
    focus_sentence = _extract_last_sentence(story)
    language_code = normalize_language(language or "en")
    return _build_prompt(
        "ascii_art.md",
        language=language_code,
        genre=genre or "a timeless adventure",
        setting=setting or "an open setting",
        story_context=story,
        focus_sentence=focus_sentence,
        width=target_width,
        height=target_height,
    )


def build_storybook_prompt(
    source_story: str,
    *,
    correction_notes: str | None = None,
    genre: str | None = None,
    setting: str | None = None,
    opening: str | None = None,
    normality_level: str | None = None,
    language_level: str | None = None,
    language: str | None = None,
) -> str:
    correction_block = (
        'Apply the following corrections as explicit priorities:\n"{0}"'
        .format(correction_notes)
        if correction_notes
        else "No corrections requested."
    )
    language_code = normalize_language(language)
    genre_text = genre or "selected genre"
    setting_text = setting or "selected setting"
    opening_text = opening or "selected opening"
    normality_text = normality_level or "selected normality level"
    language_level_text = language_level or "selected language level"
    return _build_prompt(
        "storybook.md",
        language=language_code,
        source_story=source_story,
        genre=genre_text,
        setting=setting_text,
        opening=opening_text,
        normality_level=normality_text,
        language_level=language_level_text,
        correction_notes=correction_block,
    )


def build_openings_prompt(
    *,
    genre: str,
    setting: str,
    normality_level: str = "Balanced",
    language_level: str = "Conversational",
    count: int = 10,
    language: str | None = None,
    random_marker: str | None = None,
) -> str:
    language_code = normalize_language(language)
    marker = random_marker or str(random.randrange(100_000, 1_000_000))
    return _build_prompt(
        "openings.md",
        language=language_code,
        genre=genre,
        setting=setting,
        normality_level=normality_level,
        language_level=language_level,
        count=str(count),
        random_marker=marker,
    )


def _build_prompt(name: str, *, language: str, **values: object) -> str:
    template = _load_template(name)
    return _replace_placeholders(
        template,
        language=language_display_name(language),
        **values,
    )


def _extract_last_sentence(story: str) -> str:
    stripped = story.strip()
    if not stripped:
        return ""

    match = re.findall(r"[^.!?]*[.!?]", stripped)
    if not match:
        return stripped

    return match[-1].strip()


@lru_cache(maxsize=None)
def _load_template(name: str) -> str:
    path = PROMPT_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Prompt template not found: {path}")
    return path.read_text().strip()


def _replace_placeholders(template: str, **values: object) -> str:
    formatted = template
    for key, value in values.items():
        formatted = formatted.replace("{" + key + "}", str(value))
    return formatted


def _regeneration_avoidance_instruction(
    avoid_continuations: tuple[str, str] | None,
) -> str:
    if not avoid_continuations:
        return ""

    option_a, option_b = avoid_continuations
    if not option_a and not option_b:
        return ""

    if option_a == option_b:
        return (
            "For this regeneration, avoid returning that exact previous option text. "
            f'Avoid "{option_a}".'
        )

    return (
        "For this regeneration, avoid repeating the exact option text from the previous turn. "
        f'"{option_a}" and "{option_b}" should both be avoided.'
    )
