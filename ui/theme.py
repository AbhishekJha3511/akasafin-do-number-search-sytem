"""
theme.py
========
Centralised theme management for DONSS.
Resolves colour tokens, drives CustomTkinter appearance,
and exposes helper methods consumed by all UI components.
"""

from __future__ import annotations

import logging
from typing import Dict

import customtkinter as ctk

from core.constants import DARK_COLORS, LIGHT_COLORS

logger = logging.getLogger(__name__)


class ThemeManager:
    """
    Manages the active colour palette and CustomTkinter appearance mode.

    Usage::

        tm = ThemeManager("dark")
        bg = tm.c("bg")          # → "#0f172a"
        tm.set_theme("light")
    """

    _VALID_THEMES = ("dark", "light", "system")

    def __init__(self, theme: str = "dark") -> None:
        self._theme: str = ""
        self._colors: Dict[str, str] = {}
        self.set_theme(theme)

    # ── Public API ─────────────────────────────────────────────

    @property
    def theme(self) -> str:
        """Current theme name."""
        return self._theme

    def c(self, key: str) -> str:
        """
        Resolve a colour token to a hex string.

        Args:
            key: Token name (e.g. "bg", "primary", "text_muted").

        Returns:
            Hex colour string, or "#000000" if the token is unknown.
        """
        color = self._colors.get(key, "#000000")
        if color == "#000000" and key not in self._colors:
            logger.warning("Unknown colour token: %s", key)
        return color

    def set_theme(self, theme: str) -> None:
        """
        Switch the active theme.

        Args:
            theme: "dark", "light", or "system".
        """
        if theme not in self._VALID_THEMES:
            logger.warning("Invalid theme '%s'; defaulting to 'dark'", theme)
            theme = "dark"

        self._theme = theme

        # Resolve "system" → actual dark/light using CTk's detection
        effective = theme
        if theme == "system":
            try:
                detected = ctk.get_appearance_mode()  # "Dark" or "Light" (pre-switch)
            except Exception:  # noqa: BLE001
                detected = "Dark"
            ctk.set_appearance_mode("System")
            try:
                detected = ctk.get_appearance_mode()
            except Exception:  # noqa: BLE001
                pass
            effective = detected.lower() if detected else "dark"

        self._colors = DARK_COLORS if effective == "dark" else LIGHT_COLORS

        # Apply to CustomTkinter globally
        ctk_mode = "Dark" if effective == "dark" else "Light"
        ctk.set_appearance_mode(ctk_mode)
        ctk.set_default_color_theme("blue")

        logger.debug("Theme set to '%s' (effective: %s)", theme, effective)

    def next_theme(self) -> str:
        """
        Cycle through dark → light → dark.

        Returns:
            The name of the newly applied theme.
        """
        new = "light" if self._theme == "dark" else "dark"
        self.set_theme(new)
        return new
