from __future__ import annotations

from pathlib import Path

import pytest

from leap_tree_game.config.settings import (
    default_env_path,
    ConfigError,
    MissingConfigError,
    ProviderSettings,
    load_settings,
    write_env_file,
)


def test_load_settings_missing_env(tmp_path: Path) -> None:
    with pytest.raises(MissingConfigError):
        load_settings(tmp_path / ".env")


def test_load_settings_valid_openai_env(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "LEAP_TREE_PROVIDER=openai",
                "LEAP_TREE_MODEL=gpt-5.2",
                "OPENAI_API_KEY=sk-test",
            ]
        )
    )

    settings = load_settings(env_path)

    assert settings.provider == "openai"
    assert settings.model == "gpt-5.2"
    assert settings.openai_api_key == "sk-test"
    assert settings.logfire_token is None


def test_load_settings_rejects_unsupported_provider(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "LEAP_TREE_PROVIDER=bogus",
                "LEAP_TREE_MODEL=model",
            ]
        )
    )

    with pytest.raises(ConfigError):
        load_settings(env_path)


def test_ollama_local_does_not_require_api_key() -> None:
    settings = ProviderSettings(
        provider="ollama",
        model="qwen3",
        ollama_base_url="http://localhost:11434/v1",
    )

    assert settings.ollama_api_key is None
    assert settings.logfire_token is None


def test_write_env_file_uses_simple_key_value_format(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    write_env_file(
        ProviderSettings(
            provider="ollama",
            model="qwen3",
            ollama_base_url="http://localhost:11434/v1",
            logfire_token="lf-token",
        ),
        env_path,
    )

    text = env_path.read_text()
    assert "LEAP_TREE_PROVIDER=ollama" in text
    assert "OLLAMA_BASE_URL=http://localhost:11434/v1" in text
    assert "LOGFIRE_TOKEN=" in text
    assert "LOGFIRE_TOKEN=lf-token" in text


def test_load_settings_loads_optional_logfire_token(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "LEAP_TREE_PROVIDER=openai",
                "LEAP_TREE_MODEL=gpt-5.2",
                "OPENAI_API_KEY=sk-test",
                "LOGFIRE_TOKEN=lf-token",
            ]
        )
    )

    settings = load_settings(env_path)

    assert settings.logfire_token == "lf-token"

def test_default_env_path_is_in_home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    home_dir = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home_dir))

    assert default_env_path() == home_dir / ".leaptreegame" / ".env"


def test_default_env_path_read_write_cycle(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    home_dir = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home_dir))
    settings = ProviderSettings(
        provider="openai",
        model="gpt-5.2",
        openai_api_key="sk-test-default",
    )
    write_env_file(settings)

    loaded = load_settings()

    assert loaded == settings
