# Leap Tree Game

A small Python 3.12+ CLI story game. Pick a genre, setting, and opening, then choose between two AI-generated continuation branches.

## Install

```bash
python3 -m pip install -r requirements.txt
```

## Configure

```bash
python -m leap_tree_game.app setup
```

The setup wizard writes `.env` with one of the supported providers:

- `openai`
- `anthropic`
- `ollama`

Local Ollama does not require an API key when using `http://localhost:11434/v1`.

## Play

```bash
python -m leap_tree_game.app
```

Useful commands:

```bash
python -m leap_tree_game.app --help
python -m leap_tree_game.app doctor
python -m leap_tree_game.app setup
python -m leap_tree_game.app play
```

## Test

```bash
python -m pytest
```

The unit tests do not make live AI requests. Live provider smoke tests are intentionally left out of the MVP test path.
