# Requirements

Leap Tree Game is a text-based CLI game in which a player chooses a genre, setting, and story opening. The AI then presents the unchanged current story and provides two continuation options.

The player selects one option, that option's continuation text is appended to the current story, and the AI provides two new continuation options from the updated story. The cycle repeats indefinitely.

Please see the prompt templates:

- [prompts/initial.md](prompts/initial.md) — initial prompt template for the MVP.
- [prompts/next.md](prompts/next.md) — subsequent prompt template for the MVP.

## UI Requirements

- CLI application
- Allow selecting predefined options or entering a custom “Other” option
- Render each setup question and each story-choice turn on a fresh terminal screen
- The setup wizard must render each question on a fresh terminal screen, including separate screens for:
  - provider selection,
  - model entry,
  - API key entry.
- Put a muted frame around every screen, similar to Claude Code's framed terminal layout
- Use colors and/or bold text for different sections such as:
  - current story
  - player choices
  - prompts/errors
- The UI should feel clean, spacious, and modern, somewhat similar to Claude Code
- The story and choices should render on each turn in one framed screen.
- Render the ASCII scene above the story text on each turn, derived from a separate model query and using the full available frame width with an explicitly calculated target height for remaining space.
- Generate ASCII scenes from the most recent sentence while preserving continuity with the full story context.
- The rendered ASCII scene must be image-only (no prose, no labels, no story text, no markdown, no preamble).
- The bottom footer should show the current state as: `turn <N> | <provider> / <model> | tokens used: <count>`, where provider/model are lower-case labels by runtime summary and token count reflects cumulative usage.

## Game Flow

1. The player launches the application
2. The player selects an AI provider/model and enters API keys
3. The player fills out CLI forms for the initial prompt
4. The AI outputs the selected opening unchanged as the current story and generates two continuation options
5. The player selects one continuation, or chooses regenerate (`g`) to request a new pair of options for the same turn
6. The selected continuation is appended to the current story
7. The full story history is sent to the AI on every turn
8. When regenerate is used, requested options should avoid repeating the previous exact pair
9. Steps 4-8 repeat continuously until the player exits the application

## Technical Requirements

- Language: Python 3.12+
- Framework: Pydantic AI
- CLI libraries:
  - `Typer` for commands and CLI interactions
  - `Rich` for terminal formatting and interactive UI screens
- Maintain `.env.example` file
- Use an environment file (`.env`) to configure:
  - AI provider
  - model name
  - API keys
- If no `.env` file exists, provide a CLI setup wizard to generate one
- Supported providers:
  - OpenAI
  - Anthropic
  - Ollama

## AI Response Format

AI responses must always follow a structured JSON format.

Example:

```json
{
  "story": "Current story so far",
  "option_a": "First continuation text",
  "option_b": "Second continuation text"
}
```

The application must validate AI responses before rendering them in the UI.

The `story` field is the canonical story-so-far. On the first turn, it must be exactly the player's selected opening, unchanged. On later turns, it must be the previous canonical story plus the continuation the player selected. The model must not rewrite, summarize, or expand `story` outside the selected continuation path.

The `option_a` and `option_b` fields are not labels such as "Take the sword" or instructions to the player. They are the actual continuation text that could be appended to `story` if selected. For example, after the opening `On a perfectly ordinary impossible day`, the UI should look like:

Each continuation option should be 3-7 words so choices stay quick to scan. The app should choose the first sentence-ending instruction with 50% probability, then alternate instructions on later AI requests so the game has a visible 50/50 balance:

- The options should be the end of the sentence.
- The options should not end the sentence.

On regeneration (`g`), keep the existing sentence-shape for that turn so a period-ending mode does not unexpectedly change.

If the current story ends a sentence, each continuation option must start with a capital letter before it is rendered or appended.
The prompt must also include a concrete beginning instruction derived from the current story text: if the current story ends a sentence, instruct options to start a new sentence; otherwise, instruct options to continue the previous sentence.
The app must enforce the selected sentence-ending instruction after model validation: remove terminal sentence punctuation for the "should not end the sentence" mode, and ensure terminal sentence punctuation for the "should be the end of the sentence" mode.

```text
On a perfectly ordinary impossible day

A. a brass cloud knocked politely.
B. the town clock ran backward.
```

If the player selects `A`, the next turn's canonical story becomes:

```text
On a perfectly ordinary impossible day a brass cloud knocked politely.
```

## Context Handling

- The full story history must always be included in every AI request
- The current story must always be rebuilt by appending selected continuation options, not by accepting unrelated model rewrites
- There is no context limit for the MVP
- Story history should not be summarized

## Error Handling

The application must gracefully handle:

- Invalid API keys
- Missing `.env` configuration
- Malformed AI responses
- Empty AI responses
- Network failures
- API rate limits

Error messages should be user-friendly and clearly explain how to recover or retry.
- If the provider returns a model-level 404 response, explain that the configured model may be unavailable to this account and direct the player to setup and select another model.

## Application Scope

This project is intentionally a MVP.

The following features are explicitly out of scope:

- save/load game functionality
- moderation/content filtering
- authentication/accounts
- multiplayer support
- database persistence
- story summarization

## Project Structure

Suggested structure:

```text
/docs
/prompts
/leap-tree-game
  /game
  /ui
  /models
  /config
  app.py
/tests
.env.example
requirements.txt
README.md
```

## Exit Flow

The player must be able to:

- quit the game
- restart the game from the beginning

## Testing Requirements

Include:

- unit tests
- AI response parsing tests
- prompt formatting tests

## Packaging

The application should be runnable with:

```bash
python leap-tree-game/app.py
```

Optionally:

```bash
pip install -r requirements.txt
```
