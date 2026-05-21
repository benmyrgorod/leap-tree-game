"""Game setup and turn history models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from leap_tree_game.models.story import StoryResponse

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

    def full_story_history(self) -> str:
        """Return the complete story and choice history without summarization."""

        lines = [
            f"Genre: {self.setup.genre}",
            f"Setting: {self.setup.setting}",
            f"Opening: {self.setup.opening}",
        ]

        for index, turn in enumerate(self.turns, start=1):
            lines.append(f"Turn {index} story: {turn.story}")
            lines.append(f"Turn {index} option A: {turn.option_a}")
            lines.append(f"Turn {index} option B: {turn.option_b}")
            if turn.choice is not None:
                lines.append(
                    f"Turn {index} selected option {turn.choice.label}: {turn.choice.text}"
                )

        return "\n".join(lines)
