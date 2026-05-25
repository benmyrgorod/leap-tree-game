"""Environment-backed provider settings."""

from __future__ import annotations

import os
import stat
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

ProviderName = Literal["openai", "anthropic", "ollama"]

SUPPORTED_PROVIDERS: tuple[ProviderName, ...] = ("openai", "anthropic", "ollama")
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434/v1"
DEFAULT_MODELS: dict[ProviderName, str] = {
    "openai": "gpt-5.2",
    "anthropic": "claude-sonnet-4-5",
    "ollama": "qwen3",
}


class MissingConfigError(FileNotFoundError):
    """Raised when the `.env` configuration file is not present."""


class ConfigError(ValueError):
    """Raised when provider settings are invalid."""


class ProviderSettings(BaseModel):
    """Provider settings read from `.env`."""

    model_config = ConfigDict(str_strip_whitespace=True)

    provider: ProviderName
    model: str = Field(min_length=1)
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    ollama_base_url: str = DEFAULT_OLLAMA_BASE_URL
    ollama_api_key: str | None = None
    logfire_token: str | None = None

    @field_validator("provider", mode="before")
    @classmethod
    def normalize_provider(cls, value: str) -> str:
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator(
        "openai_api_key",
        "anthropic_api_key",
        "ollama_api_key",
        "logfire_token",
        mode="before",
    )
    @classmethod
    def empty_string_to_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = str(value).strip()
        return value or None

    @model_validator(mode="after")
    def validate_provider_requirements(self) -> "ProviderSettings":
        if self.provider == "openai" and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for the OpenAI provider.")
        if self.provider == "anthropic" and not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for the Anthropic provider.")
        if self.provider == "ollama":
            if not self.ollama_base_url:
                raise ValueError("OLLAMA_BASE_URL is required for the Ollama provider.")
            if self.uses_ollama_cloud and not self.ollama_api_key:
                raise ValueError("OLLAMA_API_KEY is required for Ollama Cloud.")
        return self

    @property
    def uses_ollama_cloud(self) -> bool:
        return self.provider == "ollama" and "ollama.com" in self.ollama_base_url.lower()

    @property
    def provider_model(self) -> str:
        return f"{self.provider}:{self.model}"

    def summary(self) -> str:
        return f"{self.provider} / {self.model}"


def default_env_path() -> Path:
    return Path.home() / ".leaptreegame" / ".env"


def load_settings(env_path: Path | str | None = None) -> ProviderSettings:
    path = _resolve_env_path(env_path)
    if not path.exists():
        raise MissingConfigError(f"No configuration file found at {path}.")

    values = _read_dotenv(path)
    data = {
        "provider": values.get("LEAP_TREE_PROVIDER", ""),
        "model": values.get("LEAP_TREE_MODEL", ""),
        "openai_api_key": values.get("OPENAI_API_KEY"),
        "anthropic_api_key": values.get("ANTHROPIC_API_KEY"),
        "ollama_base_url": values.get("OLLAMA_BASE_URL") or DEFAULT_OLLAMA_BASE_URL,
        "ollama_api_key": values.get("OLLAMA_API_KEY"),
        "logfire_token": values.get("LOGFIRE_TOKEN") or values.get("LOGFIRE_API_KEY"),
    }

    try:
        settings = ProviderSettings.model_validate(data)
    except ValidationError as exc:
        raise ConfigError(_format_validation_error(exc)) from exc

    _load_env_into_process(path)
    return settings


def write_env_file(settings: ProviderSettings, env_path: Path | str | None = None) -> None:
    path = _resolve_env_path(env_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        ("LEAP_TREE_PROVIDER", settings.provider),
        ("LEAP_TREE_MODEL", settings.model),
        ("OPENAI_API_KEY", settings.openai_api_key or ""),
        ("ANTHROPIC_API_KEY", settings.anthropic_api_key or ""),
        ("OLLAMA_BASE_URL", settings.ollama_base_url),
        ("OLLAMA_API_KEY", settings.ollama_api_key or ""),
        ("LOGFIRE_TOKEN", settings.logfire_token or ""),
    ]
    path.write_text("\n".join(f"{key}={_clean_env_value(value)}" for key, value in lines) + "\n")
    try:
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass


def _resolve_env_path(env_path: Path | str | None) -> Path:
    return default_env_path() if env_path is None else Path(env_path)


def _read_dotenv(path: Path) -> dict[str, str]:
    try:
        from dotenv import dotenv_values
    except ImportError:
        return _read_dotenv_without_dependency(path)

    return {key: value or "" for key, value in dotenv_values(path).items()}


def _read_dotenv_without_dependency(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _load_env_into_process(path: Path) -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        for key, value in _read_dotenv_without_dependency(path).items():
            os.environ.setdefault(key, value)
        return

    load_dotenv(dotenv_path=path, override=False)


def _clean_env_value(value: str) -> str:
    if "\n" in value or "\r" in value:
        raise ValueError("Environment values may not contain newlines.")
    return value.strip()


def _format_validation_error(exc: ValidationError) -> str:
    messages = []
    for error in exc.errors():
        location = ".".join(str(part) for part in error["loc"]) or "settings"
        messages.append(f"{location}: {error['msg']}")
    return "; ".join(messages)

