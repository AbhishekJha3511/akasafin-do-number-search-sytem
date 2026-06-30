"""
widgets.py
==========
Reusable, self-contained UI components for DONSS.
All widgets accept a ThemeManager instance for consistent styling.
"""

from __future__ import annotations

import logging
from typing import Callable, Dict, Optional, Tuple

import customtkinter as ctk

from ui.theme import ThemeManager

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# SUMMARY CARD  — ultra-compact single-line strip
# ─────────────────────────────────────────────

class SummaryCard(ctk.CTkFrame):
    """
    A compact metric card: icon · value · label in one tight row.
    Height is fixed at 44px so the cards row never wastes vertical space.
    """

    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        tm: ThemeManager,
        icon: str = "📊",
        label: str = "Metric",
        **kwargs,
    ) -> None:
        super().__init__(
            parent,
            fg_color=tm.c("card_bg"),
            corner_radius=8,
            border_width=1,
            border_color=tm.c("border"),
            height=44,
            **kwargs,
        )
        self.pack_propagate(False)   # enforce fixed height
        self._tm = tm

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")

        # Icon
        ctk.CTkLabel(
            inner,
            text=icon,
            font=ctk.CTkFont(size=15),
            text_color=tm.c("primary"),
            width=22,
        ).grid(row=0, column=0, padx=(0, 6))

        # Value
        self._value_lbl = ctk.CTkLabel(
            inner,
            text="—",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=tm.c("text"),
            anchor="w",
        )
        self._value_lbl.grid(row=0, column=1, sticky="w")

        # Separator dot
        ctk.CTkLabel(
            inner,
            text="·",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=tm.c("text_dim"),
        ).grid(row=0, column=2, padx=4)

        # Label
        self._label_lbl = ctk.CTkLabel(
            inner,
            text=label,
            font=ctk.CTkFont(family="Segoe UI", size=9),
            text_color=tm.c("text_muted"),
            anchor="w",
        )
        self._label_lbl.grid(row=0, column=3, sticky="w")

    def set_value(self, value: str) -> None:
        """Update the displayed metric value."""
        self._value_lbl.configure(text=value)

    def set_label(self, label: str) -> None:
        """Update the card sub-label."""
        self._label_lbl.configure(text=label)


# ─────────────────────────────────────────────
# FIELD ROW  (label + value as CTkLabel — NO scrollbar)
# ─────────────────────────────────────────────

class FieldRow(ctk.CTkFrame):
    """
    A horizontal label-value pair inside a detail panel.

    Uses CTkLabel (not CTkEntry) for the value so there is absolutely
    no internal scrollbar or extra chrome. Height is fixed at 26px so
    many rows fit without overflowing the panel.
    """

    # Fixed row height — tweak this one number to resize all rows
    ROW_H: int = 26

    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        tm: ThemeManager,
        label: str,
        small: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(
            parent,
            fg_color="transparent",
            height=self.ROW_H,
            **kwargs,
        )
        self.pack_propagate(False)   # keep fixed height
        self._tm = tm
        self._small = small
        self._value_var = ""         # store current text

        self.columnconfigure(0, minsize=140)
        self.columnconfigure(1, weight=1)

        lbl_font = ctk.CTkFont(
            family="Segoe UI",
            size=8 if small else 13,
            weight="bold",
        )
        val_font = ctk.CTkFont(
            family="Segoe UI",
            size=8 if small else 14,
            weight="bold" if not small else "normal",
        )

        # Label column
        ctk.CTkLabel(
            self,
            text=label + " :",
            font=lbl_font,
            text_color=tm.c("text_muted"),
            anchor="w",
            width=140,
        ).grid(row=0, column=0, sticky="w", padx=(2, 6))

        # Value column — plain Label, no scrollbar ever
        self._value_lbl = ctk.CTkLabel(
            self,
            text="",
            font=val_font,
            fg_color=tm.c("surface2"),
            text_color=tm.c("primary") if small else tm.c("text"),
            corner_radius=4,
            anchor="w",
            padx=6,
        )
        self._value_lbl.grid(row=0, column=1, sticky="ew", padx=(0, 2), pady=1)

    def set_value(self, value: str) -> None:
        """Update the displayed value."""
        self._value_var = value
        self._value_lbl.configure(text=value)

    def get_value(self) -> str:
        """Return the current displayed value."""
        return self._value_var

    def clear(self) -> None:
        """Clear the displayed value."""
        self._value_var = ""
        self._value_lbl.configure(text="")


# ─────────────────────────────────────────────
# DETAIL PANEL  (titled card, no scrollbar)
# ─────────────────────────────────────────────

class DetailPanel(ctk.CTkFrame):
    """
    A titled card containing a column of FieldRow widgets.
    No scrollbar — all rows are always visible.
    """

    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        tm: ThemeManager,
        title: str = "",
        **kwargs,
    ) -> None:
        super().__init__(
            parent,
            fg_color=tm.c("card_bg"),
            corner_radius=10,
            border_width=1,
            border_color=tm.c("border"),
            **kwargs,
        )
        self._tm = tm
        self._rows: Dict[str, FieldRow] = {}
        self._hidden_keys: set = set()

        # ── Title bar ─────────────────────────────────────────
        if title:
            title_frame = ctk.CTkFrame(
                self, fg_color=tm.c("surface2"), corner_radius=0, height=28
            )
            title_frame.pack(fill="x")
            title_frame.pack_propagate(False)
            ctk.CTkLabel(
                title_frame,
                text=title,
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                text_color=tm.c("text"),
                anchor="w",
            ).pack(side="left", padx=10, pady=4)

        # ── Content frame — plain, no scrollbar ───────────────
        self._content = ctk.CTkFrame(self, fg_color="transparent")
        self._content.pack(fill="both", expand=True, padx=6, pady=4)
        self._content.columnconfigure(0, weight=1)

    # ── Field builders ─────────────────────────────────────────

    def add_field(self, key: str, label: str, small: bool = False) -> FieldRow:
        """Add a single FieldRow to the panel."""
        row = FieldRow(self._content, self._tm, label=label, small=small)
        row.pack(fill="x", pady=0)
        self._rows[key] = row
        return row

    def add_pair(
        self,
        key1: str, label1: str,
        key2: str, label2: str,
    ) -> Tuple[FieldRow, FieldRow]:
        """Add two FieldRows side-by-side."""
        pair = ctk.CTkFrame(self._content, fg_color="transparent")
        pair.pack(fill="x", pady=0)
        pair.columnconfigure(0, weight=1)
        pair.columnconfigure(1, weight=1)

        r1 = FieldRow(pair, self._tm, label=label1)
        r1.grid(row=0, column=0, sticky="ew", padx=(0, 3))
        self._rows[key1] = r1

        r2 = FieldRow(pair, self._tm, label=label2)
        r2.grid(row=0, column=1, sticky="ew", padx=(3, 0))
        self._rows[key2] = r2

        return r1, r2

    # ── Data API ───────────────────────────────────────────────

    def set_field(self, key: str, value: str) -> None:
        """Set the value of a named FieldRow."""
        if key in self._rows:
            self._rows[key].set_value(value)

    def get_field(self, key: str) -> str:
        """Get the current value of a named FieldRow."""
        return self._rows[key].get_value() if key in self._rows else ""

    def clear_all(self) -> None:
        """Clear all FieldRow values."""
        for row in self._rows.values():
            row.clear()

    # ── Visibility ─────────────────────────────────────────────

    def show_row(self, key: str) -> None:
        """Make a hidden FieldRow visible again."""
        if key in self._rows and key in self._hidden_keys:
            self._rows[key].pack(fill="x", pady=0)
            self._hidden_keys.discard(key)

    def hide_row(self, key: str) -> None:
        """Hide a FieldRow from view."""
        if key in self._rows and key not in self._hidden_keys:
            self._rows[key].pack_forget()
            self._hidden_keys.add(key)

    def set_row_visible(self, key: str, visible: bool) -> None:
        """Show or hide a row by key."""
        if visible:
            self.show_row(key)
        else:
            self.hide_row(key)


# ─────────────────────────────────────────────
# TOOLBAR BUTTON
# ─────────────────────────────────────────────

class ToolbarButton(ctk.CTkButton):
    """Compact toolbar button with icon + label."""

    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        tm: ThemeManager,
        icon: str,
        label: str,
        command: Optional[Callable] = None,
        color_key: str = "surface2",
        hover_key: str = "border",
        width: int = 110,
        **kwargs,
    ) -> None:
        super().__init__(
            parent,
            text=f"{icon}  {label}",
            font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
            fg_color=tm.c(color_key),
            hover_color=tm.c(hover_key),
            text_color=tm.c("text"),
            corner_radius=7,
            height=30,
            width=width,
            command=command,
            **kwargs,
        )


# ─────────────────────────────────────────────
# STATUS BAR
# ─────────────────────────────────────────────

class StatusBar(ctk.CTkFrame):
    """Slim footer bar showing status message and progress bar."""

    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        tm: ThemeManager,
        **kwargs,
    ) -> None:
        super().__init__(
            parent,
            fg_color=tm.c("statusbar_bg"),
            corner_radius=0,
            height=28,
            **kwargs,
        )
        self._tm = tm
        self.pack_propagate(False)

        self._status_var = ctk.StringVar(value="Ready")
        self._status_lbl = ctk.CTkLabel(
            self,
            textvariable=self._status_var,
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=tm.c("text_muted"),
            anchor="w",
        )
        self._status_lbl.pack(side="left", padx=12)

        self._progress = ctk.CTkProgressBar(
            self,
            width=180,
            height=6,
            corner_radius=3,
            progress_color=tm.c("primary"),
            fg_color=tm.c("surface2"),
        )
        self._progress.pack(side="right", padx=12)
        self._progress.set(0)

        self._progress_lbl = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=tm.c("primary"),
        )
        self._progress_lbl.pack(side="right", padx=4)

    def set_status(self, message: str, color_key: str = "text_muted") -> None:
        """Update the status message."""
        self._status_var.set(message)
        self._status_lbl.configure(text_color=self._tm.c(color_key))

    def set_progress(self, fraction: float, label: str = "") -> None:
        """Update the progress bar (0.0 → 1.0)."""
        self._progress.set(max(0.0, min(1.0, fraction)))
        self._progress_lbl.configure(text=label)

    def reset_progress(self) -> None:
        """Reset progress bar to zero."""
        self._progress.set(0)
        self._progress_lbl.configure(text="")
