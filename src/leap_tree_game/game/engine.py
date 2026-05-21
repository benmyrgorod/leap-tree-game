"""Interactive game loop."""

from __future__ import annotations

import textwrap

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

    @staticmethod
    def _estimate_wrapped_lines(text: str, width: int) -> int:
        safe_width = max(1, width)
        wrapped = textwrap.wrap(text, width=safe_width, break_long_words=False, break_on_hyphens=False)
        return max(1, len(wrapped))

    def play(self) -> None:
        while True:
            state = GameState(
                setup=ask_game_setup(
                    console=self.console,
                    provider_summary=self.settings.summary(),
                )
            )
            next_turn = 1
            response = self._generate_with_retry(
                lambda: self.story_client.generate_initial(state.setup),
                turn_number=next_turn,
            )
            if response is None:
                return
            state.append_response(
                response,
                continuation_shape=self._shape_from_response(response),
            )
            self._render_turn(response, turn_number=next_turn)

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
                        lambda: self._generate_regenerated_turn_with_retry(state),
                        turn_number=max(len(state.turns), 1),
                    )
                    if response is None:
                        return
                    state.replace_latest_turn(
                        response,
                        continuation_shape=self._shape_from_turn(state.turns[-1]),
                    )
                    self._render_turn(response, turn_number=len(state.turns))
                    continue

                if command == "a":
                    label = "A"
                else:
                    label = "B"
                choice = state.choose(label)
                turn_number = len(state.turns) + 1
                response = self._generate_with_retry(
                    lambda choice=choice: self.story_client.generate_next(state, choice),
                    turn_number=turn_number,
                )
                if response is None:
                    return
                state.append_response(
                    response,
                    continuation_shape=self._shape_from_response(response),
                )
                self._render_turn(response, turn_number=turn_number)

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

    def _render_turn(self, response, *, turn_number: int) -> None:
        ascii_art = self._generate_with_retry(
            lambda: self.story_client.generate_ascii_art(
                response.story,
                width=self._art_width(),
                height=self._art_height(response),
            ),
            status_message="[dim]Generating ASCII scene...[/dim]",
            ask_to_retry=False,
            turn_number=turn_number,
        )
        render_turn_screen(
            response,
            active_console=self.console,
            subtitle=self._turn_status(turn_number),
            ascii_art=ascii_art,
        )

    def _turn_status(self, turn_number: int) -> str:
        return (
            f"turn {turn_number} | "
            f"{self.settings.summary()} | "
            f"tokens used: {self.story_client.total_tokens}"
        )

    def _art_width(self) -> int:
        return max(40, (self.console.width or 100) - 4)

    def _art_height(self, response) -> int:
        total_lines = self.console.height or 24
        frame_width = self._art_width()
        non_art_lines = self._estimated_non_art_line_count(response, frame_width)
        available = total_lines - non_art_lines
        return max(3, available - 4)

    @staticmethod
    def _choices_command_lines(width: int) -> int:
        command = "Choose: a (first option), b (second option), g (regenerate), r (restart), q (quit)"
        command_body_lines = max(1, len(
            textwrap.wrap(
                command,
                width=max(1, width),
                break_long_words=False,
                break_on_hyphens=False,
            )
        ))
        return 1 + command_body_lines

    def _estimated_non_art_line_count(self, response, width: int) -> int:
        # Outer frame lines are always visible regardless of art presence.
        outer_lines = 4

        story_text_width = max(24, width - 6)
        story_text_lines = self._estimate_wrapped_lines(response.story, width=story_text_width)
        story_panel_lines = story_text_lines + 4

        option_width = max(24, width - 14)
        option_lines = max(
            self._estimate_wrapped_lines(response.option_a, option_width),
            self._estimate_wrapped_lines(response.option_b, option_width),
        )
        # Build options includes one intentionally blank first row.
        choices_lines = (option_lines * 2) + 1

        command_lines = self._choices_command_lines(max(24, width - 4))

        return outer_lines + story_panel_lines + choices_lines + command_lines

    def _generate_with_retry(
        self,
        operation,
        *,
        status_message: str = "[dim]Asking the story engine...[/dim]",
        ask_to_retry: bool = True,
        turn_number: int | None = None,
    ):
        while True:
            try:
                with self.console.status(status_message):
                    return operation()
            except StoryGenerationError as exc:
                if turn_number is None:
                    render_error(str(exc), active_console=self.console)
                else:
                    render_error(
                        f"turn {turn_number}: {str(exc)}",
                        active_console=self.console,
                    )
                if not ask_to_retry:
                    return None
                if not Confirm.ask("Retry?", default=True, console=self.console):
                    return None
