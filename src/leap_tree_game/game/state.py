"""Game setup and turn history models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from leap_tree_game.models.story import StoryResponse
from leap_tree_game.game.text import append_continuation

ChoiceLabel = Literal["A", "B"]


class NonEmptyTextModel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("*", mode="after")
    @classmethod
    def reject_blank_strings(cls, value):
        if isinstance(value, str) and not value.strip():
            raise ValueError("must not be empty")
        return value


class GameSetup(NonEmptyTextModel):
    genre: str
    setting: str
    opening: str


class Choice(NonEmptyTextModel):
    label: ChoiceLabel
    text: str


class StoryTurn(NonEmptyTextModel):
    """One branching point in the story.

    `story` is the canonical story before the player picks the next continuation.
    The selected option text is appended only after the choice is made.
    """

    story: str
    option_a: str
    option_b: str
    choice: Choice | None = None

    @classmethod
    def from_response(cls, response: StoryResponse) -> "StoryTurn":
        return cls(
            story=response.story,
            option_a=response.option_a,
            option_b=response.option_b,
        )

    def option_text(self, label: ChoiceLabel) -> str:
        return self.option_a if label == "A" else self.option_b


class GameState(BaseModel):
    setup: GameSetup
    turns: list[StoryTurn] = Field(default_factory=list)

    def append_response(self, response: StoryResponse) -> StoryTurn:
        turn = StoryTurn.from_response(response)
        self.turns.append(turn)
        return turn

    def choose(self, label: ChoiceLabel) -> Choice:
        if not self.turns:
            raise ValueError("Cannot choose before the first story turn exists.")
        turn = self.turns[-1]
        choice = Choice(label=label, text=turn.option_text(label))
        turn.choice = choice
        return choice

    def current_story(self) -> str:
        """Return the canonical story with selected continuations appended."""

        story = self.setup.opening
        for turn in self.turns:
            story = turn.story
            if turn.choice is not None:
                story = append_continuation(story, turn.choice.text)
        return story

    def full_story_history(self) -> str:
        """Return the complete story and choice history without summarization."""

        lines = [
            f"Genre: {self.setup.genre}",
            f"Setting: {self.setup.setting}",
            f"Opening: {self.setup.opening}",
            f"Current story so far: {self.current_story()}",
        ]

        for index, turn in enumerate(self.turns, start=1):
            lines.append(f"Turn {index} story before choice: {turn.story}")
            lines.append(f"Turn {index} option A continuation: {turn.option_a}")
            lines.append(f"Turn {index} option B continuation: {turn.option_b}")
            if turn.choice is not None:
                story_after_choice = append_continuation(turn.story, turn.choice.text)
                lines.append(
                    f"Turn {index} selected option {turn.choice.label} continuation: {turn.choice.text}"
                )
                lines.append(f"Turn {index} story after choice: {story_after_choice}")

        return "\n".join(lines)

