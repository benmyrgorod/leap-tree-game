"""Interactive game loop orchestration."""

from __future__ import annotations

import re
import secrets
from datetime import datetime
from pathlib import Path
from typing import Callable, TypeVar

from rich.console import Console
from rich.prompt import Confirm, Prompt

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
    render_full_story_screen,
    render_success,
    render_turn_screen,
    render_warning,
)
from leap_tree_game.ui.forms import ask_choice_command, ask_storybook_command
from leap_tree_game.ui.screens import ask_game_setup
from leap_tree_game.i18n import t

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
            setup = ask_game_setup(
                console=self.console,
                provider_summary=self.settings.summary(),
                opening_options_provider=self._generate_opening_options,
            )
            if setup is None:
                return
            state = GameState(setup=setup)

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
            command = ask_choice_command(
                console=self.console,
                language=state.setup.language,
            )

            if command == "q":
                render_success(
                    t(state.setup.language, "turn.goodbye"),
                    active_console=self.console,
                )
                return False
            if command == "m":
                action = self._show_full_story(state)
                if action == "restart":
                    return True
                if action == "quit":
                    return False
                continue
            if command == "s":
                render_success(
                    t(state.setup.language, "turn.restart"),
                    active_console=self.console,
                )
                return True
            if command == "r":
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

    def _show_full_story(self, state: GameState) -> str:
        language = state.setup.language
        source_story = state.current_story()
        status_message: str | None = None
        status_message_style = "green"
        story = self._normalize_story_text(
            self._generate_storybook_with_retry(
                source_story=source_story,
                language=language,
            )
        )
        if story is None:
            return "continue"

        while True:
            render_full_story_screen(
                story,
                active_console=self.console,
                subtitle=self._turn_status(
                    turn_number=state.turn_count,
                    language=language,
                ),
                command_text=t(language, "turn.storybook_command_help"),
                status_message=status_message,
                status_message_style=status_message_style,
                language=language,
            )
            status_message = None
            status_message_style = "green"

            command = ask_storybook_command(
                console=self.console,
                language=language,
            )
            if command == "q":
                render_success(
                    t(language, "turn.goodbye"),
                    active_console=self.console,
                )
                return "quit"
            if command == "s":
                render_success(
                    t(language, "turn.restart"),
                    active_console=self.console,
                )
                return "restart"
            if command == "w":
                path = self._save_story_to_disk(state, story)
                if path is None:
                    status_message = t(language, "turn.story_save_failed")
                    status_message_style = "red"
                else:
                    status_message = t(language, "turn.story_saved", path=path)
                    status_message_style = "green"
                continue

            if command == "r":
                regenerated = self._generate_storybook_with_retry(
                    source_story=source_story,
                    language=language,
                )
                if regenerated is None:
                    return "continue"
                story = self._normalize_story_text(regenerated)
                continue

            if command == "e":
                correction_notes = Prompt.ask(
                    t(language, "turn.story_edit_prompt"),
                    default="",
                    show_default=False,
                    console=self.console,
                ).strip()
                if not correction_notes:
                    continue
                regenerated = self._generate_storybook_with_retry(
                    source_story=source_story,
                    correction_notes=correction_notes,
                    language=language,
                )
                if regenerated is None:
                    return "continue"
                story = self._normalize_story_text(regenerated)
                continue

            render_warning(
                f"Unsupported story command: {command}",
                active_console=self.console,
            )

    def _save_story_to_disk(self, state: GameState, story: str) -> str | None:
        stories_dir = self._stories_dir()
        stories_dir.mkdir(parents=True, exist_ok=True)
        while True:
            path = stories_dir / self._safe_story_filename(state)
            if not path.exists():
                break
        try:
            path.write_text(story, encoding="utf-8")
        except OSError:
            return None
        return str(path)

    @staticmethod
    def _normalize_story_text(story: str | None) -> str | None:
        if story is None:
            return None
        return story.strip()

    def _stories_dir(self) -> Path:
        return Path.home() / ".leaptreegame" / "stories"

    def _safe_story_filename(self, state: GameState) -> str:
        genre = self._slugify(state.setup.genre, fallback="story")
        setting = self._slugify(state.setup.setting, fallback="story")
        language = self._slugify(state.setup.language, fallback="lang")
        date_token = datetime.now().strftime("%Y%m%d")
        hash_token = secrets.token_hex(3)
        return f"{date_token}_{language}_{genre}_{setting}_{hash_token}.txt"

    @staticmethod
    def _slugify(value: str, *, fallback: str = "story") -> str:
        slug = re.sub(r"[^a-z0-9]+", "_", value.strip().lower())
        slug = slug.strip("_")
        if not slug:
            return fallback
        return slug[:32]

    def _start_initial_turn(self, state: GameState) -> StoryResponse | None:
        response = self._generate_with_retry(
            lambda: self.story_client.generate_initial(
                state.setup,
                language=state.setup.language,
            ),
            turn_number=state.next_turn_number(),
            status_language=state.setup.language,
        )
        if response is None:
            return None
        return response

    def _generate_opening_options(
        self,
        genre: str,
        setting: str,
        normality_level: str,
        language_level: str,
        language: str,
    ) -> list[str] | None:
        return self._generate_with_retry(
            lambda: self.story_client.generate_openings(
                genre=genre,
                setting=setting,
                normality_level=normality_level,
                language_level=language_level,
                language=language,
            ),
            status_message="engine.generating_openings",
            status_language=language,
        )

    def _generate_next_turn_with_retry(
        self,
        state: GameState,
        choice: Choice,
        *,
        turn_number: int,
    ) -> StoryResponse | None:
        return self._generate_with_retry(
            lambda: self.story_client.generate_next(
                state,
                choice,
                language=state.setup.language,
            ),
            status_language=state.setup.language,
            turn_number=turn_number,
        )

    def _generate_storybook_with_retry(
        self,
        source_story: str,
        *,
        correction_notes: str | None = None,
        language: str = "en",
    ) -> str | None:
        return self._generate_with_retry(
            lambda: self.story_client.generate_storybook(
                source_story,
                correction_notes=correction_notes,
                language=language,
            ),
            status_message="engine.generating_storybook",
            status_language=language,
            turn_number=None,
            ask_to_retry=True,
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
                    language=state.setup.language,
                )
            return self.story_client.generate_next(
                state,
                previous_choice,
                avoid_continuations=avoid,
                continuation_shape=continuation_shape,
                language=state.setup.language,
            )

        return self.story_client.generate_next(
            state,
            last_turn.choice,
            avoid_continuations=avoid,
            continuation_shape=continuation_shape,
            language=state.setup.language,
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
        art_height = self._art_height(
            response,
            language=state.setup.language,
        )
        art_width = self._art_width()
        ascii_art = self._generate_with_retry(
            lambda: self.story_client.generate_ascii_art(
                response.story,
                genre=state.setup.genre,
                setting=state.setup.setting,
                language=state.setup.language,
                width=art_width,
                height=art_height,
            ),
            status_message="engine.generating_ascii",
            status_language=state.setup.language,
            ask_to_retry=False,
            turn_number=turn_number,
        )

        render_turn_screen(
            response,
            active_console=self.console,
            subtitle=self._turn_status(
                turn_number=turn_number,
                language=state.setup.language,
            ),
            language=state.setup.language,
            ascii_art=ascii_art,
        )

    def _turn_status(
        self,
        turn_number: int,
        *,
        language: str = "en",
    ) -> str:
        return self.layout.turn_status_label(
            turn_number,
            self.settings.summary(),
            self.story_client.total_tokens,
            language=language,
            status_label=t(
                language,
                "status.turn",
                turn_number=turn_number,
                provider_summary=self.settings.summary(),
                tokens_used=self.story_client.total_tokens,
            ),
        )

    def _art_width(self) -> int:
        return self.layout.art_width()

    def _art_height(self, response: StoryResponse, language: str = "en") -> int:
        return self.layout.art_height(
            response.story,
            response.option_a,
            response.option_b,
            language=language,
            command_text=t(language, "layout.command_help"),
        )

    def _estimated_non_art_line_count(self, response: StoryResponse, width: int) -> int:
        return self.layout.estimated_non_art_line_count(
            response.story,
            response.option_a,
            response.option_b,
            width=width,
            language="en",
            command_text=t("en", "layout.command_help"),
        )

    def _generate_with_retry(
        self,
        operation: Callable[[], T],
        *,
        status_message: str = "engine.asking",
        status_language: str = "en",
        ask_to_retry: bool = True,
        turn_number: int | None = None,
    ) -> T | None:
        while True:
            try:
                with self.console.status(
                    f"[dim]{t(status_language, status_message)}[/dim]"
                ):
                    return operation()
            except StoryGenerationError as exc:
                if turn_number is None:
                    render_error(str(exc), active_console=self.console)
                else:
                    render_error(
                        t(
                            status_language,
                            "status.turn",
                            turn_number=turn_number,
                            provider_summary=self.settings.summary(),
                            tokens_used=self.story_client.total_tokens,
                        )
                        + f": {str(exc)}",
                        active_console=self.console,
                    )
                if not ask_to_retry:
                    return None
                if not Confirm.ask(
                    t(status_language, "turn.retry_prompt"),
                    default=True,
                    console=self.console,
                ):
                    return None
