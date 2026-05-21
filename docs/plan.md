# Implementation Plan

Leap Tree Game will start as a small Python 3.12+ CLI MVP: the player configures an AI provider, chooses a genre, setting, and opening, then repeatedly selects between two AI-generated continuation options. The implementation should keep the selected opening and accumulated story path canonical, stay narrow and testable, and remain easy to run with `python leap-tree-game/app.py`.

## References

- Project requirements: [requirements.md](requirements.md)
- MVP initial prompt: [prompts/initial.md](prompts/initial.md)
- MVP next-turn prompt: [prompts/next.md](prompts/next.md)
- Pydantic AI model/provider concepts: [Pydantic AI models overview](https://pydantic.dev/docs/ai/models/overview/)
- Pydantic AI structured output modes: [Pydantic AI output docs](https://pydantic.dev/docs/ai/core-concepts/output/)
- Ollama provider details: [Pydantic AI Ollama docs](https://pydantic.dev/docs/ai/models/ollama/)

## MVP Architecture

Use a small package under `src/` so the CLI entrypoint stays thin and business logic is testable.

```text
docs/
prompts/
  initial.md
  next.md
leap-tree-game/
  __init__.py
  app.py
  config/
    __init__.py
    settings.py
    setup_wizard.py
  game/
    __init__.py
    engine.py
    prompts.py
    state.py
  models/
    __init__.py
    story.py
  providers/
    __init__.py
    agent.py
  ui/
    __init__.py
    console.py
    forms.py
    screens.py
tests/
  test_config.py
  test_prompt_formatting.py
  test_story_response.py
  test_game_state.py
.env.example
requirements.txt
README.md
```

## Core Data Model

Define the AI response as the contract between the model and UI:

```python
class StoryResponse(BaseModel):
    story: str
    option_a: str
    option_b: str
```

`story` is the current canonical story-so-far, not newly generated branch prose. On the first turn it must be exactly the selected opening unchanged. On later turns it must be the previous canonical story plus the continuation selected by the player. The app should normalize this field from local state after parsing a valid response, so a model cannot rewrite the opening or silently jump to an unselected branch.

`option_a` and `option_b` are the actual branch continuations that may be appended to `story`; they are not action labels or summaries. A correct first response for the opening `On a perfectly ordinary impossible day` should read conceptually like:

```text
On a perfectly ordinary impossible day

A. a brass cloud knocked politely.
B. the town clock ran backward.
```

Add internal models for:

- `GameSetup`: selected `genre`, `setting`, and `opening`.
- `Choice`: selected label and text.
- `StoryTurn`: canonical story before the next choice, continuation options, and the choice that followed it.
- `GameState`: setup, ordered turns, helpers to build full unsummarized story history, and helpers to derive the current canonical story by appending selected continuations.
- `ProviderSettings`: provider, model name, and provider-specific connection settings.

Validation should reject empty `story`, `option_a`, and `option_b`, because the UI cannot recover from blank continuation choices.

## Configuration

Create `.env.example` with clear provider-specific variables:

```dotenv
LEAP_TREE_PROVIDER=openai
LEAP_TREE_MODEL=gpt-5.2

OPENAI_API_KEY=
ANTHROPIC_API_KEY=

OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_API_KEY=
```

Implementation notes:

- Load `.env` at startup.
- If `.env` is missing, launch a Typer/Rich setup wizard.
- The setup wizard should ask each question on a separate framed screen, including provider selection, model entry, and provider credential entry.
- The wizard should ask for provider, model name, and only the API key or base URL needed for that provider.
- Write `.env` with restrictive, simple key-value formatting.
- Validate that provider is one of `openai`, `anthropic`, or `ollama`.
- Do not require API keys for local Ollama unless the user is configuring Ollama Cloud or another authenticated endpoint.

## AI Provider Layer

Create a single `create_story_agent(settings)` function that returns a configured Pydantic AI agent using `StoryResponse` as the output type.

Implementation approach:

- Keep all Pydantic AI imports and provider-specific construction inside `providers/agent.py`.
- Use Pydantic AI model/provider shorthands where possible, but hide those details behind the local factory.
- Prefer schema-backed structured output for providers that support it reliably.
- For self-hosted Ollama, prefer native JSON-schema output when available.
- Keep a fallback parse-and-validate path so malformed or partial model output becomes a friendly error instead of a traceback.

The game engine should not know whether the selected model is OpenAI, Anthropic, or Ollama. It should only call a local `StoryClient.generate_next(...)`.

## Prompt Handling

Move the initial prompt language into `prompts/initial.md` and `prompts/next.md`, then normalize them into implementation-ready templates.

Prompt builder responsibilities:

- Include selected genre, setting, and opening on the first turn.
- Include the full unsummarized story history on every subsequent turn.
- Include the current canonical story-so-far on every subsequent turn.
- Include the player’s selected option for next-turn requests.
- Instruct the model to return only the structured JSON object matching `StoryResponse`.
- Ask for two short, contrasting continuation options, each 3-7 words, that can be appended directly to `story`.
- The prompt builder should choose the first sentence-ending instruction with 50% probability, then alternate instructions on later AI requests so the game has a visible 50/50 balance: either options should be the end of the sentence, or options should not end the sentence.
- Normalize continuation options after model validation so options start with a capital letter when the current story ends a sentence.
- Programmatically add a concrete beginning instruction to each prompt: start a new sentence when the current story has ended a sentence, otherwise continue the previous sentence.
- Enforce the selected sentence-ending instruction after model validation, because providers may ignore prompt wording: strip terminal `.`, `!`, or `?` for "should not end the sentence" and add a period when needed for "should be the end of the sentence".
- Instruct the model to keep `story` unchanged from the provided current story and put all new branch prose in `option_a` and `option_b`.
- Avoid Markdown formatting requirements inside JSON values; Rich can handle terminal styling after validation.

Keep predefined options in code constants so tests can cover them and the UI can render them consistently:

- Genres from `prompts/initial.md`
- Settings from `prompts/initial.md`
- Story openings from `prompts/initial.md`

Each list should include an `Other` path that accepts custom player input.

## CLI Flow

Use Typer for commands and Rich for the interactive terminal UI.

Initial command:

```bash
python leap-tree-game/app.py
```

Recommended commands:

- `play`: default command that starts or resumes the normal launch flow.
- `setup`: regenerate `.env`.
- `doctor`: validate Python version, `.env`, provider settings, and basic import availability.

Runtime flow:

1. Render app title and provider/model summary.
2. If config is missing or invalid, run setup wizard (provider, model, API key step-by-step).
3. Prompt for genre, setting, and story opening.
4. Generate the first story response, with `story` equal to the selected opening.
5. Render the current story and two continuation choices.
6. Prompt for A, B, restart, or quit.
7. Append the selected continuation text to the canonical story in game state.
8. Generate the next story response with full history and current canonical story.
9. Repeat until the player quits or restarts.

## Rich UI Design

The terminal should feel clean and spacious without becoming visually busy.

Use:

- A muted header with app name, provider, and model.
- A fresh terminal screen for each setup question and each story-choice turn.
- A muted full-screen frame around each question screen, similar to Claude Code.
- Rich panels for story text.
- Clear A/B choice rows with bold labels.
- Color-coded status lines for prompts, warnings, and recoverable errors.
- A framed area that renders the current story and choice set.
- Short commands at choice prompts: `a`, `b`, `r`, `q`.

Render choices only after the final `StoryResponse` validates.

## Error Handling

Add a small error translation layer that maps low-level exceptions into user-facing recovery messages.

Handle:

- Missing `.env`: offer setup wizard.
- Invalid provider/model configuration: explain which field is wrong.
- Invalid or missing API key: tell the player to rerun setup or edit `.env`.
- Network failure: offer retry or quit.
- Rate limit: tell the player to wait, retry, or switch provider/model.
- Empty model response: offer retry.
- Malformed model response: show a friendly validation failure and offer retry.
- Keyboard interrupt: exit cleanly.

Do not show raw stack traces during normal play. Keep detailed exception logging optional for a future debug mode.

## Testing Plan

Use `pytest` for fast unit tests that do not require live API calls.

Required coverage:

- `StoryResponse` accepts valid JSON and rejects empty fields.
- Prompt builders include genre, setting, opening, full history, and selected choice.
- Game state preserves complete story history without summarization.
- Config loader handles missing `.env`, valid `.env`, unsupported provider, and Ollama without API key.
- CLI form helpers return custom `Other` values.
- Provider layer can be tested with Pydantic AI test/fake models rather than real network calls.

Live provider smoke tests should be optional and skipped unless the needed API key or Ollama server is configured.

## Implementation Phases

### Phase 1: Project Scaffold

- Create `requirements.txt`.
- Create `.env.example`.
- Create package folders under `leap-tree-game`.
- Add `leap-tree-game/app.py` Typer entrypoint.
- Add a short README with install and run commands.

Acceptance criteria:

- `python leap-tree-game/app.py --help` works.
- `pip install -r requirements.txt` installs the declared runtime dependencies.

### Phase 2: Models, Config, and Setup

- Implement Pydantic models for story response, game state, and provider settings.
- Implement `.env` loading.
- Implement setup wizard that writes `.env`.
- Implement `doctor` command.

Acceptance criteria:

- Missing config launches setup or reports a clear setup instruction.
- Invalid provider names fail with a friendly message.
- Unit tests cover config parsing.

### Phase 3: Prompt Builders

- Move prompt templates into `prompts/`.
- Implement initial-turn and next-turn prompt builders.
- Implement option constants and `Other` handling.

Acceptance criteria:

- Prompt tests prove the full story history is included on every request.
- Prompt tests prove the current canonical story includes the selected continuation.
- Prompt tests prove the selected option is included on next-turn requests.

### Phase 4: AI Client

- Implement Pydantic AI agent factory.
- Implement `StoryClient.generate_initial(...)`.
- Implement `StoryClient.generate_next(...)`.
- Implement response validation and user-facing error translation.

Acceptance criteria:

- Fake-model tests can produce a valid `StoryResponse`.
- Malformed output becomes a recoverable game error.

### Phase 5: Interactive Game Loop

- Build Rich forms for genre, setting, and opening.
- Build story and choice rendering.
- Build repeat loop with `a`, `b`, `r`, and `q`.
- Add framed turn rendering updates for every response.

Acceptance criteria:

- The user can start a new story and continue for multiple turns.
- Restart clears state and returns to setup forms.
- Quit exits without a traceback.

### Phase 6: Polish and Release Readiness

- Add README usage examples.
- Add optional live-provider smoke test instructions.
- Run lint/type checks if added.
- Verify fresh clone path: install dependencies, create `.env`, run game, quit cleanly.

Acceptance criteria:

- `pytest` passes.
- `python leap-tree-game/app.py` launches the game.
- The MVP stays within the explicit out-of-scope boundaries: no save/load, no database, no auth, no multiplayer, no summarization.

## Suggested Dependency Set

Start with a plain `requirements.txt`:

```text
pydantic>=2
pydantic-ai
python-dotenv
rich
typer
pytest
```

Add provider extras only if needed after verifying the selected Pydantic AI install path. Keep dependency changes minimal until the first working CLI loop exists.

## First Build Order

1. Scaffold package and commands.
2. Add models and prompt builders with tests.
3. Add config loading and setup wizard.
4. Add fake AI client path so the game loop can be built without API keys.
5. Add real Pydantic AI provider wiring.
6. Add framed, screen-refresh turn rendering.
7. Add recovery paths and final docs.

This order keeps the terminal game playable early while isolating the highest-risk integration work behind a small provider layer.
