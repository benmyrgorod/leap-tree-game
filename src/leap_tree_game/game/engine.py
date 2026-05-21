"""Interactive game loop."""

from __future__ import annotations

from rich.console import Console
from rich.prompt import Confirm

from leap_tree_game.config.settings import ProviderSettings
from leap_tree_game.game.state import Choice, GameState
from leap_tree_game.providers.agent import StoryClient, StoryGenerationError
from leap_tree_game.ui.console import (
    render_choices,
    render_error,
    render_header,
    render_streamed_story,
    render_success,
    render_warning,
)
from leap_tree_game.ui.forms import ask_choice_command
from leap_tree_game.ui.screens import ask_game_setup


class GameEngine:
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
        render_header(self.settings, active_console=self.console)

        while True:
            state = GameState(setup=ask_game_setup(console=self.console))
            response = self._generate_with_retry(
                lambda: self.story_client.generate_initial(state.setup)
            )
            if response is None:
                return
            state.append_response(response)
            self._render_turn(response)

            while True:
                command = ask_choice_command(console=self.console)
                if command == "q":
                    render_success("Goodbye.", active_console=self.console)
                    return
                if command == "r":
                    render_warning("Restarting story.", active_console=self.console)
                    break

                label = "A" if command == "a" else "B"
                choice = state.choose(label)
                response = self._generate_with_retry(
                    lambda choice=choice: self.story_client.generate_next(state, choice)
                )
                if response is None:
                    return
                state.append_response(response)
                self._render_turn(response)

    def _render_turn(self, response) -> None:
        render_streamed_story(response, active_console=self.console)
        render_choices(response, active_console=self.console)
        self.console.print("[dim]Commands: a, b, r, q[/dim]")

    def _generate_with_retry(self, operation):
        while True:
            try:
                with self.console.status("[dim]Asking the story engine...[/dim]"):
                    return operation()
            except StoryGenerationError as exc:
                render_error(str(exc), active_console=self.console)
                if not Confirm.ask("Retry?", default=True, console=self.console):
                    return None
