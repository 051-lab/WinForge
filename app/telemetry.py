"""WinForge telemetry - privacy-respecting opt-in usage tracking."""
from __future__ import annotations
import json
import platform
import uuid
from pathlib import Path
from typing import Any, Dict
from loguru import logger
import app

_STATE_FILE = Path("config/telemetry.json")
_CONSENT_KEY = "telemetry_enabled"


def _load_state() -> Dict[str, Any]:
    """Load persisted telemetry state from disk."""
    if _STATE_FILE.exists():
        try:
            return json.loads(_STATE_FILE.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("Failed to read telemetry state: {}", exc)
    return {_CONSENT_KEY: False, "install_id": None}


def _save_state(state: Dict[str, Any]) -> None:
    """Persist telemetry state to disk."""
    try:
        _STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        _STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except Exception as exc:
        logger.warning("Failed to save telemetry state: {}", exc)


def is_enabled() -> bool:
    """Return True only if the user has explicitly opted in."""
    return bool(_load_state().get(_CONSENT_KEY, False))


def set_enabled(value: bool) -> None:
    """Opt in (True) or opt out (False). Always persists the user's choice."""
    state = _load_state()
    state[_CONSENT_KEY] = bool(value)
    if value and not state.get("install_id"):
        state["install_id"] = str(uuid.uuid4())
    _save_state(state)
    logger.info("Telemetry opt-in set to: {}", value)


def get_install_id() -> str | None:
    """Return the anonymous install UUID, or None if not opted in."""
    state = _load_state()
    if not state.get(_CONSENT_KEY, False):
        return None
    return state.get("install_id")


def collect_event(event: str, extra: Dict[str, Any] | None = None) -> Dict[str, Any] | None:
    """Build a telemetry payload. Returns None if opt-in is off.
    No data is transmitted - this just structures the payload for
    future use (log shipping, etc.). All fields are non-personal.
    """
    if not is_enabled():
        logger.debug("Telemetry disabled; skipping event '{}'.", event)
        return None
    payload: Dict[str, Any] = {
        "event": event,
        "version": app.__version__,
        "install_id": get_install_id(),
        "platform": platform.system(),
        "python": platform.python_version(),
    }
    if extra:
        payload.update(extra)
    logger.debug("Telemetry event: {}", payload)
    return payload
