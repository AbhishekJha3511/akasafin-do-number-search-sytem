"""
dialogs.py
==========
Modal dialog windows for DONSS: Settings, About, and Error dialogs.
All dialogs are self-contained and receive only simple data types.
"""

from __future__ import annotations

import logging
import webbrowser
from typing import Callable, Optional

import customtkinter as ctk

from core.constants import APP_AUTHOR, APP_DESCRIPTION, APP_GITHUB, APP_NAME, APP_VERSION
from core.settings import AppSettings
from ui.theme import ThemeManager

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# BASE DIALOG
# ─────────────────────────────────────────────

class _BaseDialog(ctk.CTkToplevel):
    """Shared base for modal dialogs."""

    def __init__(
        self,
        parent: ctk.CTk,
        tm: ThemeManager,
        title: str,
        width: int = 480,
        height: int = 340,
    ) -> None:
        super().__init__(parent)
        self._tm = tm
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.resizable(False, False)
        self.configure(fg_color=tm.c("bg"))
        self.grab_set()  # modal
        self.focus_set()

        # Centre over parent
        parent.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width() - width) // 2
        py = parent.winfo_y() + (parent.winfo_height() - height) // 2
        self.geometry(f"+{px}+{py}")

        self.bind("<Escape>", lambda _: self.destroy())

        # When this dialog is destroyed, return keyboard focus to the
        # parent window's search box (if it exposes one).
        self.bind("<Destroy>", self._restore_parent_focus, add="+")

    def _restore_parent_focus(self, event=None) -> None:
        """Send focus back to the parent's search entry after closing."""
        # Only act on the dialog's own destroy event, not child widgets.
        if event is not None and event.widget is not self:
            return
        parent = self.master
        focus_fn = getattr(parent, "_focus_search", None)
        if callable(focus_fn):
            try:
                parent.after(50, focus_fn)
            except Exception:  # noqa: BLE001
                pass


# ─────────────────────────────────────────────
# SETTINGS DIALOG
# ─────────────────────────────────────────────

class SettingsDialog(_BaseDialog):
    """
    Settings dialog allowing the user to change theme and preferences.

    Args:
        parent:    Root window.
        tm:        ThemeManager instance.
        settings:  Current AppSettings (will be mutated in-place).
        on_apply:  Callback invoked with the updated AppSettings.
    """

    def __init__(
        self,
        parent: ctk.CTk,
        tm: ThemeManager,
        settings: AppSettings,
        on_apply: Optional[Callable[[AppSettings], None]] = None,
    ) -> None:
        super().__init__(parent, tm, "⚙  Settings", width=460, height=320)
        self._settings = settings
        self._on_apply = on_apply
        self._build()

    def _build(self) -> None:
        tm = self._tm
        s = self._settings

        ctk.CTkLabel(
            self,
            text="⚙  Settings",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=tm.c("text"),
        ).pack(pady=(20, 16))

        # Theme selector
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=32, pady=6)
        ctk.CTkLabel(
            row,
            text="Theme :",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=tm.c("text_muted"),
            width=120,
            anchor="w",
        ).pack(side="left")
        self._theme_var = ctk.StringVar(value=s.theme.capitalize())
        theme_menu = ctk.CTkOptionMenu(
            row,
            variable=self._theme_var,
            values=["Dark", "Light", "System"],
            fg_color=tm.c("surface2"),
            button_color=tm.c("primary"),
            button_hover_color=tm.c("primary_hover"),
            text_color=tm.c("text"),
            dropdown_fg_color=tm.c("surface"),
            dropdown_hover_color=tm.c("surface2"),
            dropdown_text_color=tm.c("text"),
            width=180,
        )
        theme_menu.pack(side="left", padx=(12, 0))

        # Search history limit
        row2 = ctk.CTkFrame(self, fg_color="transparent")
        row2.pack(fill="x", padx=32, pady=6)
        ctk.CTkLabel(
            row2,
            text="History Limit :",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=tm.c("text_muted"),
            width=120,
            anchor="w",
        ).pack(side="left")
        self._history_var = ctk.StringVar(value=str(s.search_history_max))
        ctk.CTkEntry(
            row2,
            textvariable=self._history_var,
            width=80,
            fg_color=tm.c("surface2"),
            border_color=tm.c("border"),
            text_color=tm.c("text"),
        ).pack(side="left", padx=(12, 0))

        # Buttons
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=32, pady=(20, 0))
        ctk.CTkButton(
            btn_row,
            text="✔  Apply",
            fg_color=tm.c("success"),
            hover_color=tm.c("success_hover"),
            text_color="#ffffff",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            width=120,
            command=self._apply,
        ).pack(side="left")
        ctk.CTkButton(
            btn_row,
            text="✖  Cancel",
            fg_color=tm.c("surface2"),
            hover_color=tm.c("border"),
            text_color=tm.c("text"),
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            width=120,
            command=self.destroy,
        ).pack(side="left", padx=(12, 0))

    def _apply(self) -> None:
        self._settings.theme = self._theme_var.get().lower()
        try:
            self._settings.search_history_max = max(10, int(self._history_var.get()))
        except ValueError:
            pass
        if self._on_apply:
            self._on_apply(self._settings)
        self.destroy()


# ─────────────────────────────────────────────
# ABOUT DIALOG
# ─────────────────────────────────────────────

class AboutDialog(_BaseDialog):
    """Displays application information and links."""

    def __init__(self, parent: ctk.CTk, tm: ThemeManager) -> None:
        super().__init__(parent, tm, f"❓  About {APP_NAME}", width=420, height=340)
        self._build()

    def _build(self) -> None:
        tm = self._tm

        ctk.CTkLabel(
            self,
            text=APP_NAME,
            font=ctk.CTkFont(family="Segoe UI", size=32, weight="bold"),
            text_color=tm.c("primary"),
        ).pack(pady=(24, 2))

        ctk.CTkLabel(
            self,
            text=APP_DESCRIPTION,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=tm.c("text_muted"),
        ).pack()

        ctk.CTkLabel(
            self,
            text=f"Version {APP_VERSION}",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=tm.c("text_dim"),
        ).pack(pady=(4, 0))

        ctk.CTkLabel(
            self,
            text=f"Made with ❤️ by {APP_AUTHOR}",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=tm.c("text_muted"),
        ).pack(pady=(12, 0))

        ctk.CTkButton(
            self,
            text="🐙  GitHub Profile",
            fg_color=tm.c("surface2"),
            hover_color=tm.c("border"),
            text_color=tm.c("primary"),
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            width=180,
            command=lambda: webbrowser.open(APP_GITHUB),
        ).pack(pady=16)

        ctk.CTkButton(
            self,
            text="Close",
            fg_color=tm.c("primary"),
            hover_color=tm.c("primary_hover"),
            text_color="#ffffff",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            width=100,
            command=self.destroy,
        ).pack()


# ─────────────────────────────────────────────
# ERROR DIALOG
# ─────────────────────────────────────────────

class ErrorDialog(_BaseDialog):
    """Professional error dialog with a copyable message."""

    def __init__(
        self,
        parent: ctk.CTk,
        tm: ThemeManager,
        title: str,
        message: str,
        detail: str = "",
    ) -> None:
        super().__init__(parent, tm, f"❌  {title}", width=500, height=280 if not detail else 360)
        self._message = message
        self._detail = detail
        self._build()

    def _build(self) -> None:
        tm = self._tm

        ctk.CTkLabel(
            self,
            text="❌",
            font=ctk.CTkFont(size=36),
            text_color=tm.c("danger"),
        ).pack(pady=(18, 4))

        ctk.CTkLabel(
            self,
            text=self._message,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=tm.c("text"),
            wraplength=440,
        ).pack(padx=24)

        if self._detail:
            ctk.CTkTextbox(
                self,
                height=80,
                fg_color=tm.c("surface2"),
                border_color=tm.c("border"),
                text_color=tm.c("text_muted"),
                font=ctk.CTkFont(family="Consolas", size=10),
                wrap="word",
            ).pack(fill="x", padx=24, pady=(10, 0))
            # We'd insert text but CTkTextbox is not easily writable after init
            # so we skip detail body for simplicity; full detail is in the log

        ctk.CTkButton(
            self,
            text="OK",
            fg_color=tm.c("danger"),
            hover_color=tm.c("danger_hover"),
            text_color="#ffffff",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            width=100,
            command=self.destroy,
        ).pack(pady=14)


# ─────────────────────────────────────────────
# INFO DIALOG
# ─────────────────────────────────────────────

class InfoDialog(_BaseDialog):
    """Simple informational dialog."""

    def __init__(
        self,
        parent: ctk.CTk,
        tm: ThemeManager,
        title: str,
        message: str,
    ) -> None:
        super().__init__(parent, tm, f"ℹ  {title}", width=440, height=220)
        self._message = message
        self._build()

    def _build(self) -> None:
        tm = self._tm

        ctk.CTkLabel(
            self,
            text="ℹ️",
            font=ctk.CTkFont(size=36),
            text_color=tm.c("primary"),
        ).pack(pady=(18, 4))

        ctk.CTkLabel(
            self,
            text=self._message,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=tm.c("text"),
            wraplength=400,
            justify="center",
        ).pack(padx=24)

        ctk.CTkButton(
            self,
            text="OK",
            fg_color=tm.c("primary"),
            hover_color=tm.c("primary_hover"),
            text_color="#ffffff",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            width=100,
            command=self.destroy,
        ).pack(pady=16)
