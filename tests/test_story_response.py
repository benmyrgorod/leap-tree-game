from __future__ import annotations

import pytest
from pydantic import ValidationError

from leap_tree_game.models.story import (
    OpeningSuggestions,
    StoryResponse,
    parse_opening_suggestions,
    parse_story_response,
)


def test_story_response_accepts_valid_json() -> None:
    response = parse_story_response(
        '{"story":"The door hummed awake.","option_a":"Open it carefully","option_b":"Run into the rain"}'
    )

    assert response == StoryResponse(
        story="The door hummed awake.",
        option_a="Open it carefully",
        option_b="Run into the rain",
    )


def test_story_response_rejects_empty_fields() -> None:
    with pytest.raises(ValidationError):
        StoryResponse(story=" ", option_a="Open it carefully", option_b="Run away")


def test_story_response_extracts_json_from_wrapped_text() -> None:
    response = parse_story_response(
        'Sure.\n```json\n{"story":"A bell rang.","option_a":"Answer the bell","option_b":"Hide under stairs"}\n```'
    )

    assert response.story == "A bell rang."
    assert response.option_a == "Answer the bell"


def test_opening_suggestions_trim_and_deduplicate() -> None:
    suggestions = parse_opening_suggestions(
        {
            "openings": [
                "  The sheriff woke inside his own wanted poster. ",
                "The sheriff woke inside his own wanted poster.",
                "A chapel bell rang from under the dust.",
            ]
        }
    )

    assert suggestions == OpeningSuggestions(
        openings=[
            "The sheriff woke inside his own wanted poster.",
            "A chapel bell rang from under the dust.",
        ]
    )


def test_opening_suggestions_extracts_json_from_wrapped_text() -> None:
    suggestions = parse_opening_suggestions(
        'Here:\n```json\n{"openings":["A clock saloon served noon in cracked glasses."]}\n```'
    )

    assert suggestions.openings == [
        "A clock saloon served noon in cracked glasses."
    ]
