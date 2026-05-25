from __future__ import annotations
from types import SimpleNamespace

import pytest

import leap_tree_game.telemetry as telemetry
from leap_tree_game.config.settings import ProviderSettings
from leap_tree_game.telemetry import (
    configure_logfire,
    flush_logfire,
    logfire_event,
    logfire_span,
)


def test_configure_logfire_skips_when_no_token() -> None:
    settings = ProviderSettings(provider="openai", model="gpt-5.2", openai_api_key="sk-test")

    configure_logfire(
        settings,
        warn=lambda message: (_ for _ in ()).throw(AssertionError(message)),
    )


def test_configure_logfire_warns_when_package_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = ProviderSettings(
        provider="openai",
        model="gpt-5.2",
        openai_api_key="sk-test",
        logfire_token="lf-token",
    )
    monkeypatch.setattr(
        "leap_tree_game.telemetry.importlib.import_module",
        lambda name: (_ for _ in ()).throw(ImportError()),
    )
    warnings: list[str] = []

    configure_logfire(settings, warn=warnings.append)

    assert len(warnings) == 1
    assert "not installed" in warnings[0]


def test_configure_logfire_calls_configure_with_token(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = ProviderSettings(
        provider="openai",
        model="gpt-5.2",
        openai_api_key="sk-test",
        logfire_token="lf-token",
    )
    called: list[dict[str, object]] = []

    def configure(**kwargs):
        called.append(kwargs)

    fake_logfire = SimpleNamespace(configure=configure)

    def import_module(name: str) -> object:
        assert name == "logfire"
        return fake_logfire

    monkeypatch.setattr("leap_tree_game.telemetry.importlib.import_module", import_module)
    configure_logfire(settings)

    assert called == [{"token": "lf-token"}]


def test_configure_logfire_resets_state_when_token_missing() -> None:
    telemetry._LOGFIRE_MODULE = SimpleNamespace()  # type: ignore[assignment]
    settings = ProviderSettings(
        provider="openai",
        model="gpt-5.2",
        openai_api_key="sk-test",
    )

    configure_logfire(settings)

    assert telemetry._LOGFIRE_MODULE is None


def test_logfire_span_is_noop_when_not_configured() -> None:
    telemetry._LOGFIRE_MODULE = None

    with logfire_span("startup"):
        assert telemetry._LOGFIRE_MODULE is None


def test_logfire_span_uses_configured_module(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeSpan:
        def __init__(self, events: list[str]):
            self.events = events

        def __enter__(self):
            self.events.append("enter")
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            self.events.append("exit")
            return None

    events: list[str] = []

    def fake_span(name: str) -> FakeSpan:
        assert name == "generate"
        return FakeSpan(events)

    monkeypatch.setattr(
        "leap_tree_game.telemetry._LOGFIRE_MODULE",
        SimpleNamespace(span=fake_span),
    )

    with logfire_span("generate"):
        assert events == ["enter"]

    assert events == ["enter", "exit"]


def test_flush_logfire_tries_flush() -> None:
    calls: list[str] = []

    def fake_flush() -> None:
        calls.append("flush")

    telemetry._LOGFIRE_MODULE = SimpleNamespace(flush=fake_flush)  # type: ignore[assignment]
    flush_logfire()

    assert calls == ["flush"]


def test_flush_logfire_prefers_shutdown_if_no_flush() -> None:
    calls: list[str] = []

    def fake_shutdown() -> None:
        calls.append("shutdown")

    telemetry._LOGFIRE_MODULE = SimpleNamespace(shutdown=fake_shutdown)  # type: ignore[assignment]
    flush_logfire()

    assert calls == ["shutdown"]


def test_logfire_event_emits_when_event_supported(monkeypatch: pytest.MonkeyPatch) -> None:
    collected: list[dict[str, object]] = []

    def fake_event(name: str, **fields: object) -> None:
        collected.append({"name": name, **fields})

    telemetry._LOGFIRE_MODULE = SimpleNamespace(event=fake_event)  # type: ignore[assignment]
    logfire_event("story_client.request", output_kind="story", prompt="abc")

    assert collected == [{"name": "story_client.request", "output_kind": "story", "prompt": "abc"}]


def test_logfire_event_falls_back_to_info_if_event_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    collected: list[tuple[str, str, dict[str, object]]] = []

    def fake_info(message: str, extra: dict[str, object]) -> None:
        collected.append(("info", message, extra))

    telemetry._LOGFIRE_MODULE = SimpleNamespace(info=fake_info)  # type: ignore[assignment]
    logfire_event("story_client.response", output_kind="story")

    assert collected == [("info", "story_client.response", {"output_kind": "story"})]

