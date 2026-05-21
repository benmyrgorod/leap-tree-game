# Requirements

Leap Tree Game is a text-based CLI game in which a player chooses a genre, setting, and story opening. The AI then continues the story and provides two continuation options.

The player selects one option, the AI continues the story again with two new options, and the cycle repeats indefinitely.

Please see the prompt templates:

- [poc-prompts/01-initial-prompt.md](poc-prompts/01-initial-prompt.md) — initial prompt template for POC.
- [poc-prompts/02-next-prompt.md](poc-prompts/02-next-prompt.md) — subsequent prompt template for POC.

## UI Requirements

- CLI application
- Allow selecting predefined options or entering a custom “Other” option
- Use colors and/or bold text for different sections such as:
  - story continuation
  - player choices
  - prompts/errors
- The UI should feel clean, spacious, and modern, somewhat similar to Claude Code
- AI responses should stream progressively in the terminal

## Game Flow

1. The player launches the application
2. The player selects an AI provider/model and enters API keys
3. The player fills out CLI forms for the initial prompt
4. The AI outputs the initial story and generates two continuation options
5. The player selects one continuation
6. The full story history is sent to the AI on every turn
7. Steps 4–6 repeat continuously until the player exits the application

## Technical Requirements

- Language: Python 3.12+
- Framework: Pydantic AI
- CLI libraries:
  - `Typer` for commands and CLI interactions
  - `Rich` for terminal formatting and streaming UI
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
  "story": "Story text",
  "option_a": "First continuation option",
  "option_b": "Second continuation option"
}
```

The application must validate AI responses before rendering them in the UI.

## Context Handling

- The full story history must always be included in every AI request
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