"""Optional Logfire telemetry initialization."""

from __future__ import annotations

import importlib
from collections.abc import Callable
from contextlib import nullcontext
from typing import Any

from leap_tree_game.config.settings import ProviderSettings

_LOGFIRE_MODULE: Any | None = None


def configure_logfire(
    settings: ProviderSettings,
    *,
    warn: Callable[[str], None] | None = None,
) -> None:
    global _LOGFIRE_MODULE
    _LOGFIRE_MODULE = None
    token = settings.logfire_token
    if not token:
        return

    try:
        logfire = importlib.import_module("logfire")
    except ImportError:
        if warn is not None:
            warn(
                "Logfire is configured but the `logfire` package is not installed. "
                "Install it separately to enable telemetry: `python -m pip install logfire`."
            )
        return

    try:
        logfire.configure(token=token)
        _LOGFIRE_MODULE = logfire
    except Exception as exc:
        if warn is not None:
            warn(f"Logfire was enabled but could not be initialized: {exc}")


def logfire_span(name: str):
    """Return a span context manager when telemetry is configured."""
    if _LOGFIRE_MODULE is None:
        return nullcontext()

    try:
        return _LOGFIRE_MODULE.span(name)
    except Exception:
        return nullcontext()


def flush_logfire() -> None:
    """Flush pending telemetry events when available."""
    if _LOGFIRE_MODULE is None:
        return

    for attr in ("flush", "shutdown"):
        flusher = getattr(_LOGFIRE_MODULE, attr, None)
        if callable(flusher):
            try:
                flusher()
            except Exception:
                pass
            return


def logfire_event(message: str, **fields: object) -> None:
    """Emit a structured telemetry event when supported."""
    if _LOGFIRE_MODULE is None:
        return

    event = getattr(_LOGFIRE_MODULE, "event", None)
    if callable(event):
        try:
            event(message, **fields)
            return
        except TypeError:
            try:
                event(name=message, **fields)
                return
            except Exception:
                pass
        except Exception:
            pass

    info = getattr(_LOGFIRE_MODULE, "info", None)
    if callable(info):
        try:
            info(message, extra=fields)
            return
        except TypeError:
            try:
                info(message=message, **fields)
                return
            except Exception:
                pass
        except Exception:
            pass

    log = getattr(_LOGFIRE_MODULE, "log", None)
    if callable(log):
        try:
            log("INFO", message=message, extra=fields)
            return
        except TypeError:
            try:
                log(message=message, **fields)
            except Exception:
                pass
        except Exception:
            pass
