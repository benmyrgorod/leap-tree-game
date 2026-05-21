"""Interactive game loop."""

from __future__ import annotations

from rich.console import Console
from rich.prompt import Confirm

from leap_tree_game.config.settings import ProviderSettings
from leap_tree_game.game.state import GameState, StoryTurn
from leap_tree_game.game.prompts import ContinuationShape
from leap_tree_game.models.story import StoryResponse
from leap_tree_game.providers.agent import StoryClient, StoryGenerationError
from leap_tree_game.ui.console import (
    render_error,
    render_success,
    render_turn_screen,
    render_warning,
)
from leap_tree_game.ui.forms import ask_choice_command
from leap_tree_game.ui.screens import ask_game_setup


class GameEngine:
    _REGEN_RETRIES = 4

    def __init__(
        self,
        settings: ProviderSettings,
        *,
        story_client: StoryClient | None = None,
        console: Console,
    ) -> None:
        self.settings = settings
        self.story_client = story_client or StoryClient(settings)
        self.console = console

    def play(self) -> None:
        while True:
            state = GameState(
                setup=ask_game_setup(
                    console=self.console,
                    provider_summary=self.settings.summary(),
                )
            )
            response = self._generate_with_retry(
                lambda: self.story_client.generate_initial(state.setup)
            )
            if response is None:
                return
            state.append_response(
                response,
                continuation_shape=self._shape_from_response(response),
            )
            self._render_turn(response)

            while True:
                command = ask_choice_command(console=self.console)
                if command == "q":
                    render_success("Goodbye.", active_console=self.console)
                    return
                if command == "r":
                    render_warning("Restarting story.", active_console=self.console)
                    break
                if command == "g":
                    response = self._generate_with_retry(
                        lambda: self._generate_regenerated_turn_with_retry(state)
                    )
                    if response is None:
                        return
                    state.replace_latest_turn(
                        response,
                        continuation_shape=self._shape_from_turn(state.turns[-1]),
                    )
                    self._render_turn(response)
                    continue

                if command == "a":
                    label = "A"
                else:
                    label = "B"
                choice = state.choose(label)
                response = self._generate_with_retry(
                    lambda choice=choice: self.story_client.generate_next(state, choice)
                )
                if response is None:
                    return
                state.append_response(
                    response,
                    continuation_shape=self._shape_from_response(response),
                )
                self._render_turn(response)

    def _generate_regenerated_turn(self, state: GameState) -> StoryResponse:
        if not state.turns:
            raise ValueError("No turn exists to regenerate.")

        last_turn = state.turns[-1]
        avoid = (last_turn.option_a, last_turn.option_b)
        continuation_shape = self._shape_from_turn(last_turn)
        if last_turn.choice is None:
            previous_choice = state.latest_choice()
            if previous_choice is None:
                return self.story_client.generate_initial(
                    state.setup,
                    avoid_continuations=avoid,
                    continuation_shape=continuation_shape,
                )

            return self.story_client.generate_next(
                state,
                previous_choice,
                avoid_continuations=avoid,
                continuation_shape=continuation_shape,
            )

        # If the current turn is already selected (fallback path), regenerate from it.
        return self.story_client.generate_next(
            state,
            last_turn.choice,
            avoid_continuations=avoid,
            continuation_shape=continuation_shape,
        )

    def _generate_regenerated_turn_with_retry(self, state: GameState) -> StoryResponse:
        baseline: StoryTurn = state.turns[-1]
        last_turn_index = len(state.turns) - 1

        for attempt in range(1, self._REGEN_RETRIES + 1):
            response = self._generate_regenerated_turn(state)
            if not self._continuations_match(
                baseline.option_a,
                baseline.option_b,
                response.option_a,
                response.option_b,
            ):
                return response

            if attempt < self._REGEN_RETRIES:
                continue

            return self._warn_if_still_duplicate(
                last_turn_index=last_turn_index,
                response=response,
                attempt=attempt,
            )

    def _warn_if_still_duplicate(
        self,
        last_turn_index: int,
        response: StoryResponse,
        attempt: int,
    ) -> StoryResponse:
        if attempt >= self._REGEN_RETRIES:
            render_warning(
                (
                    f"Generated duplicate options after {attempt} attempts for turn {last_turn_index + 1}. "
                    "Using latest response."
                ),
                active_console=self.console,
        )
        return response

    @staticmethod
    def _shape_from_turn(turn: StoryTurn) -> ContinuationShape:
        if turn.continuation_shape:
            return turn.continuation_shape
        if turn.option_a.strip().endswith((".", "!", "?")) and turn.option_b.strip().endswith(
            (".", "!", "?")
        ):
            return "end_sentence"
        return "continue_sentence"

    @staticmethod
    def _shape_from_response(response: StoryResponse) -> ContinuationShape:
        if response.option_a.strip().endswith((".", "!", "?")) and response.option_b.strip().endswith(
            (".", "!", "?")
        ):
            return "end_sentence"
        return "continue_sentence"

    @staticmethod
    def _continuations_match(
        existing_a: str,
        existing_b: str,
        new_a: str,
        new_b: str,
    ) -> bool:
        normalized_baseline = {existing_a.strip().casefold(), existing_b.strip().casefold()}
        normalized_new = {new_a.strip().casefold(), new_b.strip().casefold()}
        return normalized_baseline == normalized_new

    def _render_turn(self, response) -> None:
        render_turn_screen(
            response,
            active_console=self.console,
            subtitle=self.settings.summary(),
        )

    def _generate_with_retry(self, operation):
        while True:
            try:
                with self.console.status("[dim]Asking the story engine...[/dim]"):
                    return operation()
            except StoryGenerationError as exc:
                render_error(str(exc), active_console=self.console)
                if not Confirm.ask("Retry?", default=True, console=self.console):
                    return None
