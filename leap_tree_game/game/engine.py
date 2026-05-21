"""Interactive game loop orchestration."""

from __future__ import annotations

from typing import Callable, TypeVar

from rich.console import Console
from rich.prompt import Confirm

from leap_tree_game.config.settings import ProviderSettings
from leap_tree_game.game.layout import TurnLayout
from leap_tree_game.game.logic import (
    continuation_shape_for_turn,
    continuation_shape_for_response,
    responses_match,
)
from leap_tree_game.game.state import Choice, GameState
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

T = TypeVar("T")


class GameEngine:
    """Coordinate game state, AI generation, and terminal rendering."""

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
        self.layout = TurnLayout(console=console)

    def play(self) -> None:
        while True:
            state = GameState(setup=ask_game_setup(
                console=self.console,
                provider_summary=self.settings.summary(),
            ))

            first_response = self._start_initial_turn(state)
            if first_response is None:
                return
            state.append_response(
                first_response,
                continuation_shape=continuation_shape_for_response(first_response),
            )
            self._render_turn(
                first_response,
                state=state,
                turn_number=state.next_turn_number() - 1,
            )

            if not self._play_turns(state):
                return

    def _play_turns(self, state: GameState) -> bool:
        while True:
            command = ask_choice_command(console=self.console)

            if command == "q":
                render_success("Goodbye.", active_console=self.console)
                return False
            if command == "r":
                render_warning("Restarting story.", active_console=self.console)
                return True
            if command == "g":
                regenerated = self._generate_regenerated_turn_with_retry(state)
                if regenerated is None:
                    return False
                continuation_shape = continuation_shape_for_turn(state.latest_turn)
                state.replace_latest_turn(
                    regenerated,
                    continuation_shape=continuation_shape,
                )
                self._render_turn(
                    regenerated,
                    state=state,
                    turn_number=state.turn_count,
                )
                continue

            label = "A" if command == "a" else "B"
            choice = state.choose(label)
            next_response = self._generate_next_turn_with_retry(state, choice, turn_number=state.next_turn_number())
            if next_response is None:
                return False
            state.append_response(
                next_response,
                continuation_shape=continuation_shape_for_response(next_response),
            )
            self._render_turn(
                next_response,
                state=state,
                turn_number=state.next_turn_number() - 1,
            )

    def _start_initial_turn(self, state: GameState) -> StoryResponse | None:
        response = self._generate_with_retry(
            lambda: self.story_client.generate_initial(state.setup),
            turn_number=state.next_turn_number(),
        )
        if response is None:
            return None
        return response

    def _generate_next_turn_with_retry(
        self,
        state: GameState,
        choice: Choice,
        *,
        turn_number: int,
    ) -> StoryResponse | None:
        return self._generate_with_retry(
            lambda: self.story_client.generate_next(state, choice),
            turn_number=turn_number,
        )

    def _generate_regenerated_turn_with_retry(self, state: GameState) -> StoryResponse:
        baseline = state.latest_turn
        if baseline is None:
            raise ValueError("No turn exists to regenerate.")

        last_turn_index = len(state.turns) - 1
        last_candidate: StoryResponse | None = None

        for attempt in range(1, self._REGEN_RETRIES + 1):
            last_candidate = self._generate_regenerated_turn(state)
            if not responses_match(
                baseline.option_a,
                baseline.option_b,
                last_candidate.option_a,
                last_candidate.option_b,
            ):
                return last_candidate
            if attempt < self._REGEN_RETRIES:
                continue

            self._warn_if_still_duplicate(last_turn_index, attempt)
            return last_candidate

        raise RuntimeError("Unreachable regeneration branch.")

    def _generate_regenerated_turn(self, state: GameState) -> StoryResponse:
        last_turn = state.latest_turn
        if last_turn is None:
            raise ValueError("Cannot regenerate before any turns exist.")

        avoid = (last_turn.option_a, last_turn.option_b)
        continuation_shape = continuation_shape_for_turn(last_turn)

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

        return self.story_client.generate_next(
            state,
            last_turn.choice,
            avoid_continuations=avoid,
            continuation_shape=continuation_shape,
        )

    def _warn_if_still_duplicate(
        self,
        last_turn_index: int,
        attempt: int,
    ) -> None:
        if attempt >= self._REGEN_RETRIES:
            render_warning(
                (
                    f"Generated duplicate options after {attempt} attempts for turn {last_turn_index + 1}. "
                    "Using latest response."
                ),
                active_console=self.console,
            )

    def _render_turn(
        self,
        response: StoryResponse,
        *,
        state: GameState,
        turn_number: int,
    ) -> None:
        art_height = self._art_height(response)
        art_width = self._art_width()
        ascii_art = self._generate_with_retry(
            lambda: self.story_client.generate_ascii_art(
                response.story,
                genre=state.setup.genre,
                setting=state.setup.setting,
                width=art_width,
                height=art_height,
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
        return self.layout.turn_status_label(
            turn_number,
            self.settings.summary(),
            self.story_client.total_tokens,
        )

    def _art_width(self) -> int:
        return self.layout.art_width()

    def _art_height(self, response: StoryResponse) -> int:
        return self.layout.art_height(
            response.story,
            response.option_a,
            response.option_b,
        )

    def _estimated_non_art_line_count(self, response: StoryResponse, width: int) -> int:
        return self.layout.estimated_non_art_line_count(
            response.story,
            response.option_a,
            response.option_b,
            width=width,
        )

    def _generate_with_retry(
        self,
        operation: Callable[[], T],
        *,
        status_message: str = "[dim]Asking the story engine...[/dim]",
        ask_to_retry: bool = True,
        turn_number: int | None = None,
    ) -> T | None:
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
