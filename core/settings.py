"""
settings.py
===========
Persistent application settings backed by a JSON file.
Handles theme, last folder, window geometry, and more.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass, field
from typing import Optional

from core.constants import CONFIG_FILE, WINDOW_HEIGHT, WINDOW_WIDTH

logger = logging.getLogger(__name__)


@dataclass
class AppSettings:
    """All persisted application settings."""

    # Window
    window_width: int = WINDOW_WIDTH
    window_height: int = WINDOW_HEIGHT
    window_x: Optional[int] = None
    window_y: Optional[int] = None
    window_maximized: bool = False

    # Theme: "dark" | "light" | "system"
    theme: str = "dark"

    # Data
    last_folder: str = ""

    # UI prefs
    search_history_max: int = 200
    font_size: int = 12

    def save(self) -> None:
        """Persist settings to disk."""
        try:
            os.makedirs(os.path.dirname(CONFIG_FILE) or ".", exist_ok=True)
            with open(CONFIG_FILE, "w", encoding="utf-8") as fh:
                json.dump(asdict(self), fh, indent=2)
            logger.debug("Settings saved to %s", CONFIG_FILE)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not save settings: %s", exc)

    @classmethod
    def load(cls) -> "AppSettings":
        """Load settings from disk; fall back to defaults on any error."""
        if not os.path.isfile(CONFIG_FILE):
            return cls()
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as fh:
                data: dict = json.load(fh)
            # Only keep keys that exist in the dataclass
            valid_keys = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
            filtered = {k: v for k, v in data.items() if k in valid_keys}
            return cls(**filtered)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not load settings (%s); using defaults.", exc)
            return cls()
