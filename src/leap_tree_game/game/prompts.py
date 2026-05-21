"""Prompt templates and selectable game setup options."""

from __future__ import annotations

from pathlib import Path

from leap_tree_game.game.state import Choice, GameSetup, GameState

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


def build_initial_prompt(setup: GameSetup) -> str:
    template = _load_template("initial.md")
    return _replace_placeholders(
        template,
        genre=setup.genre,
        setting=setup.setting,
        opening=setup.opening,
    )


def build_next_prompt(state: GameState, choice: Choice) -> str:
    template = _load_template("next.md")
    return _replace_placeholders(
        template,
        genre=state.setup.genre,
        setting=state.setup.setting,
        opening=state.setup.opening,
        history=state.full_story_history(),
        current_story=state.current_story(),
        choice_label=choice.label,
        choice_text=choice.text,
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
