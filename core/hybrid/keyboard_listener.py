"""Keyboard shortcut listener for in-session undo (Ctrl+Z).

Active only when the mode manager reports ``passive`` mode.  Requires
``pynput``; if the library is unavailable or cannot initialize (e.g. on a
headless CI host), the listener silently disables itself so the rest of the
application is unaffected.
"""
import logging
import threading
from typing import Callable, Optional

_log = logging.getLogger(__name__)

try:
    from pynput import keyboard as _kb  # type: ignore

    _PYNPUT_AVAILABLE = True
except Exception:
    _PYNPUT_AVAILABLE = False
    _log.warning(
        "pynput is not available; Ctrl+Z keyboard shortcut listener disabled."
    )


class KeyboardListener:
    """Listens for Ctrl+Z globally and triggers *undo_fn* in passive mode.

    Parameters
    ----------
    mode_manager:
        Any object with a ``current_mode: str`` attribute.
    undo_fn:
        Zero-argument callable invoked when Ctrl+Z is detected in passive mode.
    """

    def __init__(self, mode_manager, undo_fn: Callable[[], None]) -> None:
        self._mode_manager = mode_manager
        self._undo_fn = undo_fn
        self._listener: Optional[object] = None

    def start(self) -> None:
        """Start the global hotkey listener in a daemon thread."""
        if not _PYNPUT_AVAILABLE:
            return
        try:
            self._listener = _kb.GlobalHotKeys({"<ctrl>+z": self._on_ctrl_z})
            self._listener.daemon = True  # type: ignore[attr-defined]
            self._listener.start()  # type: ignore[attr-defined]
        except Exception as exc:
            _log.warning("Failed to start keyboard listener: %s", exc)

    def stop(self) -> None:
        """Stop the listener if it is running."""
        if self._listener is not None:
            try:
                self._listener.stop()  # type: ignore[attr-defined]
            except Exception:
                pass

    def _on_ctrl_z(self) -> None:
        """Hotkey callback — only fires undo when in passive mode."""
        if getattr(self._mode_manager, "current_mode", None) == "passive":
            try:
                self._undo_fn()
            except Exception as exc:
                _log.warning("Undo triggered by keyboard shortcut failed: %s", exc)
