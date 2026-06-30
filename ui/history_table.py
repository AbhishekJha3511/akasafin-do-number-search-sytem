"""
history_table.py
================
Search history table using ttk.Treeview, styled to match the
DONSS dark/light theme. Double-click a row to reload that record.
"""

from __future__ import annotations

import logging
import tkinter as tk
from datetime import datetime
from tkinter import ttk
from typing import Callable, List, Optional

from core.constants import HISTORY_COLUMNS
from ui.theme import ThemeManager

logger = logging.getLogger(__name__)


class HistoryTable(tk.Frame):
    """
    A themed Treeview-based table that stores search history entries.

    Args:
        parent:            Parent widget.
        tm:                ThemeManager for colour resolution.
        on_row_double_click: Callback receiving the DO Number string
                             when a row is double-clicked.
        max_rows:          Maximum number of history entries to keep.
    """

    def __init__(
        self,
        parent: tk.BaseWidget,
        tm: ThemeManager,
        on_row_double_click: Optional[Callable[[str], None]] = None,
        max_rows: int = 200,
        **kwargs,
    ) -> None:
        super().__init__(parent, bg=tm.c("surface"), **kwargs)
        self._tm = tm
        self._on_double_click = on_row_double_click
        self._max_rows = max_rows
        self._entries: List[dict] = []

        self._build_style()
        self._build_widgets()

    # ── Style ─────────────────────────────────────────────────

    def _build_style(self) -> None:
        """Configure ttk.Style for the Treeview."""
        style = ttk.Style()
        tm = self._tm

        style.theme_use("clam")

        style.configure(
            "DONSS.Treeview",
            background=tm.c("table_row_even"),
            foreground=tm.c("text"),
            fieldbackground=tm.c("table_row_even"),
            rowheight=32,
            font=("Segoe UI", 10),
            borderwidth=0,
        )
        style.configure(
            "DONSS.Treeview.Heading",
            background=tm.c("table_header"),
            foreground=tm.c("text"),
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            borderwidth=0,
        )
        style.map(
            "DONSS.Treeview",
            background=[("selected", tm.c("table_select"))],
            foreground=[("selected", tm.c("text"))],
        )
        style.map(
            "DONSS.Treeview.Heading",
            background=[("active", tm.c("primary"))],
        )

        # Scrollbar
        style.configure(
            "DONSS.Vertical.TScrollbar",
            background=tm.c("scrollbar"),
            troughcolor=tm.c("surface"),
            arrowcolor=tm.c("text_muted"),
            borderwidth=0,
        )

    # ── Widgets ───────────────────────────────────────────────

    def _build_widgets(self) -> None:
        """Build the Treeview and scrollbars."""
        tm = self._tm

        # Title bar
        title_frame = tk.Frame(self, bg=tm.c("surface2"), height=36)
        title_frame.pack(fill="x")
        title_frame.pack_propagate(False)
        tk.Label(
            title_frame,
            text="🕘  Search History",
            font=("Segoe UI", 12, "bold"),
            bg=tm.c("surface2"),
            fg=tm.c("text"),
            anchor="w",
        ).pack(side="left", padx=16, pady=6)

        self._clear_btn = tk.Button(
            title_frame,
            text="🗑  Clear History",
            font=("Segoe UI", 9, "bold"),
            bg=tm.c("danger"),
            fg="#ffffff",
            relief="flat",
            padx=10,
            cursor="hand2",
            command=self.clear,
        )
        self._clear_btn.pack(side="right", padx=12, pady=6)

        # Table frame
        table_frame = tk.Frame(self, bg=tm.c("surface"))
        table_frame.pack(fill="both", expand=True)

        # Scrollbars
        v_scroll = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            style="DONSS.Vertical.TScrollbar",
        )
        h_scroll = ttk.Scrollbar(table_frame, orient="horizontal")

        self._tree = ttk.Treeview(
            table_frame,
            columns=HISTORY_COLUMNS,
            show="headings",
            style="DONSS.Treeview",
            yscrollcommand=v_scroll.set,
            xscrollcommand=h_scroll.set,
            selectmode="browse",
        )

        # Column widths
        col_widths = {
            "Time": 110,
            "DO Number": 160,
            "Customer Name": 220,
            "Sales Executive": 180,
            "Source File": 220,
        }
        for col in HISTORY_COLUMNS:
            self._tree.heading(col, text=col, anchor="w")
            self._tree.column(col, width=col_widths.get(col, 140), anchor="w", minwidth=80)

        # Alternating row tags
        self._tree.tag_configure("odd",  background=tm.c("table_row_odd"))
        self._tree.tag_configure("even", background=tm.c("table_row_even"))

        # Layout
        v_scroll.config(command=self._tree.yview)
        h_scroll.config(command=self._tree.xview)

        self._tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        # Bind double-click
        self._tree.bind("<Double-1>", self._on_row_double_click)

    # ── Public API ─────────────────────────────────────────────

    def add_entry(
        self,
        do_number: str,
        customer_name: str,
        sales_executive: str,
        source_file: str,
    ) -> None:
        """
        Prepend a new entry to the history table.

        Args:
            do_number:      The searched DO Number.
            customer_name:  Customer name from the result.
            sales_executive: Sales executive name from the result.
            source_file:    Source Excel filename.
        """
        now = datetime.now().strftime("%H:%M:%S")
        values = (now, do_number, customer_name, sales_executive, source_file)

        # Insert at top
        self._tree.insert("", 0, values=values, tags=("even",))
        self._entries.insert(0, {"do_number": do_number, "values": values})

        # Reapply alternating row colours
        self._recolour_rows()

        # Trim to max_rows
        if len(self._entries) > self._max_rows:
            self._entries = self._entries[: self._max_rows]
            all_items = self._tree.get_children()
            for item in all_items[self._max_rows :]:
                self._tree.delete(item)

        logger.debug("History entry added: %s", do_number)

    def clear(self) -> None:
        """Remove all history entries."""
        for item in self._tree.get_children():
            self._tree.delete(item)
        self._entries.clear()
        logger.info("Search history cleared")

    # ── Private helpers ────────────────────────────────────────

    def _recolour_rows(self) -> None:
        """Apply alternating odd/even tags to all rows."""
        for i, item in enumerate(self._tree.get_children()):
            tag = "even" if i % 2 == 0 else "odd"
            self._tree.item(item, tags=(tag,))

    def _on_row_double_click(self, event: tk.Event) -> None:
        """Handle double-click on a row — invoke the reload callback."""
        selection = self._tree.selection()
        if not selection:
            return
        item = selection[0]
        values = self._tree.item(item, "values")
        if not values:
            return
        do_number = str(values[1])  # column index 1 = DO Number
        logger.info("History row double-clicked: %s", do_number)
        if self._on_double_click:
            self._on_double_click(do_number)
