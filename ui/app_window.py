"""
app_window.py
=============
Main application window for DONSS.

Assembles the complete UI:
  - Top navbar with toolbar buttons
  - Summary cards row
  - Three detail panels (Financial / Customer / Vehicle)
  - Search history table at the bottom
  - Status bar
  - All keyboard shortcuts
"""

from __future__ import annotations

import logging
import os
import threading
from tkinter import filedialog
from typing import Dict, Optional

import customtkinter as ctk

from core.constants import (
    APP_NAME,
    CUSTOMER_LAYOUT,
    DEFAULT_FALLBACK_FOLDER,
    DISPLAY_NAMES,
    LEFT_LAYOUT,
    VEHICLE_LAYOUT,
    WINDOW_HEIGHT,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
    WINDOW_WIDTH,
)
from core.data_engine import DataEngine, SearchResult
from core.settings import AppSettings
from ui.dialogs import AboutDialog, ErrorDialog, InfoDialog, SettingsDialog
from ui.history_table import HistoryTable
from ui.theme import ThemeManager
from ui.widgets import DetailPanel, StatusBar, SummaryCard, ToolbarButton

logger = logging.getLogger(__name__)


class AppWindow(ctk.CTk):
    """
    Root window for the DONSS application.

    Owns the DataEngine, ThemeManager, AppSettings, and all UI panels.
    Communicates with background threads via after() callbacks.
    """

    def __init__(self) -> None:
        super().__init__()

        # ── Core objects ───────────────────────────────────────
        self._settings: AppSettings = AppSettings.load()
        self._tm: ThemeManager = ThemeManager(self._settings.theme)
        self._engine: DataEngine = DataEngine()
        self._current_result: Optional[SearchResult] = None
        self._search_count: int = 0
        self._last_search: str = "—"

        # ── Panels registered for clear/populate ──────────────
        self._panels: Dict[str, DetailPanel] = {}

        # ── Window setup ───────────────────────────────────────
        self._setup_window()
        self._build_ui()
        self._bind_shortcuts()

        # ── Auto-load last folder ──────────────────────────────
        self.after(300, self._auto_load)

        # ── Always start with cursor in the search box ─────────
        self.after(100, self._focus_search)

        logger.info("AppWindow initialised")

    # ══════════════════════════════════════════════════════════
    # WINDOW SETUP
    # ══════════════════════════════════════════════════════════

    def _setup_window(self) -> None:
        """Configure the root window geometry, title, and appearance."""
        self.title(f"{APP_NAME}  —  DO Number Search System")

        w = self._settings.window_width
        h = self._settings.window_height

        # Centre on screen if no saved position
        if self._settings.window_x is None:
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            x = (sw - w) // 2
            y = (sh - h) // 2
        else:
            x = self._settings.window_x
            y = self._settings.window_y

        self.geometry(f"{w}x{h}+{x}+{y}")
        self.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

        if self._settings.window_maximized:
            self.state("zoomed")

        self.configure(fg_color=self._tm.c("bg"))
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ══════════════════════════════════════════════════════════
    # UI CONSTRUCTION
    # ══════════════════════════════════════════════════════════

    def _build_ui(self) -> None:
        """Build the full UI layout top to bottom."""
        self._panels = {}
        self._build_navbar()
        self._build_info_bar()
        self._build_summary_cards()
        self._build_status_bar()   # pack status bar BEFORE main area so drawer sits above it
        self._build_main_area()
        self._build_history_drawer()

    def _rebuild_ui(self) -> None:
        """
        Destroy and rebuild the entire UI using the current ThemeManager
        colours. Used to apply dark/light theme changes instantly without
        requiring an application restart.
        """
        # Preserve transient state across rebuild
        search_text = self._search_var.get() if hasattr(self, "_search_var") else ""
        current_result = self._current_result
        search_count = self._search_count
        last_search = self._last_search
        folder_text = self._folder_var.get() if hasattr(self, "_folder_var") else "Folder : None"
        was_history_visible = getattr(self, "_history_visible", False)

        # Destroy every direct child widget of the root window
        for child in self.winfo_children():
            child.destroy()

        # Re-apply window background and rebuild from scratch
        self.configure(fg_color=self._tm.c("bg"))
        self._build_ui()

        # Restore state
        self._search_var.set(search_text)
        self._folder_var.set(folder_text)
        self._current_result = current_result
        self._search_count = search_count
        self._last_search = last_search
        self._cards["card_searches"].set_value(str(search_count))
        self._cards["card_last"].set_value(last_search)

        if self._engine.is_loaded:
            self._cards["card_files"].set_value(str(self._engine.file_count))
            self._cards["card_records"].set_value(f"{self._engine.record_count:,}")
            self._cards["card_status"].set_value("Ready")

        if current_result and current_result.found:
            self._populate_panels(current_result)

        if was_history_visible:
            self._cmd_toggle_history()

        self.after(50, self._focus_search)
        logger.info("UI rebuilt for theme: %s", self._tm.theme)

    # ── Navbar ────────────────────────────────────────────────

    def _build_navbar(self) -> None:
        """Build the top navigation bar with logo, search, and toolbar."""
        tm = self._tm
        navbar = ctk.CTkFrame(
            self,
            fg_color=tm.c("navbar_bg"),
            corner_radius=0,
            height=52,
        )
        navbar.pack(fill="x", side="top")
        navbar.pack_propagate(False)

        # ── Logo ──────────────────────────────────────────────
        ctk.CTkLabel(
            navbar,
            text=APP_NAME,
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=tm.c("primary"),
        ).pack(side="left", padx=(18, 4))

        ctk.CTkLabel(
            navbar,
            text="v" + __import__("core.constants", fromlist=["APP_VERSION"]).APP_VERSION,
            font=ctk.CTkFont(family="Segoe UI", size=9),
            text_color=tm.c("text_dim"),
        ).pack(side="left", padx=(0, 16))

        _sep(navbar, tm)

        # ── Toolbar buttons (compact) ───────────────────────────
        ToolbarButton(
            navbar, tm, "📂", "Load",
            command=self._cmd_load_folder,
            color_key="success", hover_key="success_hover",
            width=68,
        ).pack(side="left", padx=2, pady=8)

        ToolbarButton(
            navbar, tm, "🔄", "Refresh",
            command=self._cmd_refresh,
            width=78,
        ).pack(side="left", padx=2, pady=8)

        ToolbarButton(
            navbar, tm, "🧹", "Clear",
            command=self._cmd_clear,
            width=66,
        ).pack(side="left", padx=2, pady=8)

        _sep(navbar, tm)

        ToolbarButton(
            navbar, tm, "📤", "Export",
            command=self._cmd_export_record,
            color_key="primary", hover_key="primary_hover",
            width=74,
        ).pack(side="left", padx=2, pady=8)

        ToolbarButton(
            navbar, tm, "📊", "All",
            command=self._cmd_export_all,
            color_key="primary", hover_key="primary_hover",
            width=58,
        ).pack(side="left", padx=2, pady=8)

        _sep(navbar, tm)

        ToolbarButton(
            navbar, tm, "⚙", "Settings",
            command=self._cmd_settings,
            width=78,
        ).pack(side="left", padx=2, pady=8)

        ToolbarButton(
            navbar, tm, "❓", "About",
            command=self._cmd_about,
            width=66,
        ).pack(side="left", padx=2, pady=8)

        self._btn_history = ToolbarButton(
            navbar, tm, "🕘", "History",
            command=self._cmd_toggle_history,
            color_key="surface2", hover_key="border",
            width=78,
        )
        self._btn_history.pack(side="left", padx=2, pady=8)

        is_dark = self._tm.theme == "dark"
        self._btn_dark_mode = ToolbarButton(
            navbar, tm,
            "☀️" if is_dark else "🌙",
            "Light" if is_dark else "Dark",
            command=self._cmd_toggle_dark_mode,
            color_key="warning" if is_dark else "surface2",
            hover_key="warning" if is_dark else "border",
            width=74,
        )
        self._btn_dark_mode.pack(side="left", padx=2, pady=8)

        # ── Right side — search FIRST (highest priority to stay visible) ──
        # Packed first on the right so it can never be squeezed out.
        ctk.CTkLabel(
            navbar,
            text="DO No :",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=tm.c("text_muted"),
        ).pack(side="right", padx=(0, 4))

        self._search_var = ctk.StringVar()
        self._search_entry = ctk.CTkEntry(
            navbar,
            textvariable=self._search_var,
            placeholder_text="Enter DO Number…",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color=tm.c("surface2"),
            border_color=tm.c("primary"),
            text_color=tm.c("text"),
            placeholder_text_color=tm.c("text_dim"),
            border_width=2,
            corner_radius=8,
            width=170,
            height=32,
        )
        self._search_entry.pack(side="right", padx=4, pady=8)
        self._search_entry.bind("<Return>", lambda _: self._cmd_search())

        _sep(navbar, tm, side="right")

        ToolbarButton(
            navbar, tm, "❌", "Exit",
            command=self._on_close,
            color_key="danger", hover_key="danger_hover",
            width=64,
        ).pack(side="right", padx=(2, 4), pady=8)

        ToolbarButton(
            navbar, tm, "🐙", "GitHub",
            command=self._cmd_open_github,
            color_key="surface2", hover_key="border",
            width=74,
        ).pack(side="right", padx=2, pady=8)

        credit = ctk.CTkLabel(
            navbar,
            text="❤️ Abhishek Jha",
            font=ctk.CTkFont(family="Segoe UI", size=9),
            text_color=tm.c("text_dim"),
        )
        credit.pack(side="right", padx=(4, 6))

    # ── Info bar ──────────────────────────────────────────────

    def _build_info_bar(self) -> None:
        """A slim bar below the navbar showing folder path."""
        tm = self._tm
        bar = ctk.CTkFrame(
            self,
            fg_color=tm.c("surface"),
            corner_radius=0,
            height=26,
        )
        bar.pack(fill="x")
        bar.pack_propagate(False)

        self._folder_var = ctk.StringVar(value="Folder : None")
        ctk.CTkLabel(
            bar,
            textvariable=self._folder_var,
            font=ctk.CTkFont(family="Segoe UI", size=9),
            text_color=tm.c("text_muted"),
            anchor="w",
        ).pack(side="left", padx=14)

    # ── Summary cards ─────────────────────────────────────────

    def _build_summary_cards(self) -> None:
        """Build the five compact KPI summary cards in a single slim row."""
        tm = self._tm
        cards_row = ctk.CTkFrame(self, fg_color=tm.c("bg"), corner_radius=0)
        cards_row.pack(fill="x", padx=12, pady=(4, 2))
        for col in range(5):
            cards_row.columnconfigure(col, weight=1)

        specs = [
            ("card_files",    "📁", "Excel Files",   "—"),
            ("card_records",  "📋", "Total Records", "—"),
            ("card_searches", "🔍", "Search Count",  "0"),
            ("card_last",     "🕐", "Last Search",   "—"),
            ("card_status",   "🟢", "Status",        "Ready"),
        ]
        self._cards: Dict[str, SummaryCard] = {}
        for col, (key, icon, label, val) in enumerate(specs):
            card = SummaryCard(cards_row, tm, icon=icon, label=label)
            card.grid(row=0, column=col, sticky="ew", padx=3, pady=2)
            card.set_value(val)
            self._cards[key] = card

    # ── Main area ─────────────────────────────────────────────

    def _build_main_area(self) -> None:
        """Build the three detail panels. History is a separate toggleable drawer."""
        tm = self._tm
        outer = ctk.CTkFrame(self, fg_color=tm.c("bg"), corner_radius=0)
        outer.pack(fill="both", expand=True, padx=12, pady=0)
        outer.columnconfigure(0, weight=1)
        outer.columnconfigure(1, weight=1)
        outer.rowconfigure(0, weight=1)

        # ── Financial panel (left) ────────────────────────────
        fin_panel = DetailPanel(outer, tm, title="  💰  Financial Details")
        fin_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 4), pady=(0, 4))
        self._panels["financial"] = fin_panel
        self._build_layout_into_panel(fin_panel, LEFT_LAYOUT)

        # ── Right container (customer + vehicle stacked) ───────
        right_col = ctk.CTkFrame(outer, fg_color="transparent")
        right_col.grid(row=0, column=1, sticky="nsew", padx=(4, 0), pady=(0, 4))
        right_col.rowconfigure(0, weight=1)
        right_col.rowconfigure(1, weight=1)
        right_col.columnconfigure(0, weight=1)

        cust_panel = DetailPanel(right_col, tm, title="  👤  Customer Details")
        cust_panel.grid(row=0, column=0, sticky="nsew", pady=(0, 4))
        self._panels["customer"] = cust_panel
        self._build_layout_into_panel(cust_panel, CUSTOMER_LAYOUT)

        veh_panel = DetailPanel(right_col, tm, title="  🚗  Vehicle Details")
        veh_panel.grid(row=1, column=0, sticky="nsew")
        self._panels["vehicle"] = veh_panel
        self._build_layout_into_panel(veh_panel, VEHICLE_LAYOUT)

    def _build_history_drawer(self) -> None:
        """
        Build the collapsible history drawer — packed BELOW the main area,
        ABOVE the status bar. Hidden by default; toggled via toolbar button.
        """
        tm = self._tm

        # Wrapper frame — this is what gets shown/hidden
        self._history_drawer = ctk.CTkFrame(
            self,
            fg_color=tm.c("surface"),
            corner_radius=0,
            height=260,
        )
        # Do NOT pack it yet — it starts hidden

        self._history = HistoryTable(
            self._history_drawer,
            tm,
            on_row_double_click=self._on_history_double_click,
            max_rows=self._settings.search_history_max,
        )
        self._history.pack(fill="both", expand=True, padx=2, pady=2)

        self._history_visible: bool = False

    def _build_layout_into_panel(self, panel: DetailPanel, layout: list) -> None:
        """
        Populate a DetailPanel from a layout spec list.

        Args:
            panel:  Target DetailPanel.
            layout: List of ("single", key) or ("pair", key1, key2) tuples.
        """
        for entry in layout:
            kind = entry[0]
            if kind == "single":
                key = entry[1]
                is_words = key == "LOAN AMOUNT WORDS"
                label = DISPLAY_NAMES.get(key, key)
                panel.add_field(key, label, small=is_words)
                # Hide battery row by default
                if key == "BATTERY TYPE ROW":
                    panel.hide_row(key)
            elif kind == "pair":
                key1, key2 = entry[1], entry[2]
                label1 = DISPLAY_NAMES.get(key1, key1)
                label2 = DISPLAY_NAMES.get(key2, key2)
                panel.add_pair(key1, label1, key2, label2)

    # ── Status bar ────────────────────────────────────────────

    def _build_status_bar(self) -> None:
        """Build the bottom status bar (packed side=bottom first)."""
        self._status_bar = StatusBar(self, self._tm)
        self._status_bar.pack(fill="x", side="bottom")

    # ══════════════════════════════════════════════════════════
    # KEYBOARD SHORTCUTS
    # ══════════════════════════════════════════════════════════

    def _bind_shortcuts(self) -> None:
        """Register global keyboard shortcuts."""
        self.bind("<Control-f>", lambda _: self._focus_search())
        self.bind("<Control-F>", lambda _: self._focus_search())
        self.bind("<Escape>", lambda _: self._on_close())

    def _focus_search(self) -> None:
        """Move keyboard focus to the search entry."""
        self._search_entry.focus_set()

    # ══════════════════════════════════════════════════════════
    # TOOLBAR COMMANDS
    # ══════════════════════════════════════════════════════════

    def _cmd_load_folder(self) -> None:
        """Open a folder picker and load all Excel files."""
        folder = filedialog.askdirectory(
            title="Select Folder Containing Excel Files",
            initialdir=self._settings.last_folder or os.path.expanduser("~"),
        )
        if not folder:
            return
        self._load_folder(folder)

    def _cmd_refresh(self) -> None:
        """Reload the last-used folder."""
        folder = self._settings.last_folder
        if not folder or not os.path.isdir(folder):
            self._show_error("Refresh Failed", "No folder has been loaded yet.")
            return
        self._load_folder(folder)

    def _cmd_clear(self) -> None:
        """Clear all field values and search entry."""
        self._search_var.set("")
        for panel in self._panels.values():
            panel.clear_all()
        # Re-hide battery row after clear
        if "vehicle" in self._panels:
            self._panels["vehicle"].hide_row("BATTERY TYPE ROW")
        self._current_result = None
        self._cards["card_status"].set_value("Cleared")
        self._status_bar.set_status("Cleared", "text_muted")
        self._focus_search()
        logger.info("Form cleared")

    def _cmd_search(self) -> None:
        """Execute a search for the current entry content."""
        do_number = self._search_var.get().strip()
        if not do_number:
            self._show_error("Search Error", "Please enter a DO Number.")
            return
        if not self._engine.is_loaded:
            self._show_error("Not Loaded", "Please load a folder first.")
            return
        self._do_search(do_number)

    def _cmd_export_record(self) -> None:
        """Export the currently displayed record to Excel."""
        if not self._current_result or not self._current_result.found:
            self._show_error("Export Error", "No record is currently displayed.")
            return
        default_name = f"DO_{self._current_result.do_number}.xlsx"
        path = filedialog.asksaveasfilename(
            title="Export Current Record",
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx")],
            initialfile=default_name,
        )
        if not path:
            return
        self._status_bar.set_status("Exporting record…", "primary")
        success = self._engine.export_record(self._current_result, path)
        if success:
            self._status_bar.set_status(f"Exported → {os.path.basename(path)}", "success")
            InfoDialog(self, self._tm, "Export Complete",
                       f"Record saved to:\n{path}")
        else:
            self._show_error("Export Failed", "Could not write the file. Check permissions.")

    def _cmd_export_all(self) -> None:
        """Export the entire loaded dataset to Excel."""
        if not self._engine.is_loaded:
            self._show_error("Export Error", "No data has been loaded.")
            return
        path = filedialog.asksaveasfilename(
            title="Export Complete Data",
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx")],
            initialfile="DONSS_Export_All.xlsx",
        )
        if not path:
            return
        self._status_bar.set_status("Exporting all data…", "primary")
        self._cards["card_status"].set_value("Exporting…")

        def _export_thread() -> None:
            success = self._engine.export_all(path)
            self.after(0, lambda: self._on_export_all_done(success, path))

        threading.Thread(target=_export_thread, daemon=True).start()

    def _on_export_all_done(self, success: bool, path: str) -> None:
        if success:
            self._status_bar.set_status(f"Export complete → {os.path.basename(path)}", "success")
            self._cards["card_status"].set_value("Exported")
            InfoDialog(self, self._tm, "Export Complete",
                       f"All {self._engine.record_count:,} records saved to:\n{path}")
        else:
            self._cards["card_status"].set_value("Export Error")
            self._show_error("Export Failed", "Could not write the file. Check permissions.")

    def _cmd_settings(self) -> None:
        """Open the Settings dialog."""
        SettingsDialog(self, self._tm, self._settings, on_apply=self._on_settings_applied)

    def _cmd_about(self) -> None:
        """Open the About dialog."""
        AboutDialog(self, self._tm)

    def _cmd_open_github(self) -> None:
        """Open the author's GitHub profile in the default browser."""
        import webbrowser
        from core.constants import APP_GITHUB
        webbrowser.open(APP_GITHUB)
        logger.info("Opened GitHub profile link")

    def _cmd_toggle_history(self) -> None:
        if self._history_visible:
            # Hide the drawer
            self._history_drawer.pack_forget()
            self._history_visible = False
            self._btn_history.configure(
                text="🕘  History",
                fg_color=self._tm.c("surface2"),
            )
            logger.info("History drawer hidden")
        else:
            # Show the drawer above the status bar, below the main area
            self._history_drawer.pack(
                fill="x",
                side="bottom",
                padx=12,
                pady=(4, 4),
                before=self._status_bar,
            )
            self._history_visible = True
            self._btn_history.configure(
                text="🕘  History ✓",
                fg_color=self._tm.c("primary"),
            )
            logger.info("History drawer shown")

    def _cmd_toggle_dark_mode(self) -> None:
        """
        Instantly switch between dark and light themes.

        Updates the ThemeManager, persists the choice to settings,
        and rebuilds the entire UI in place (no restart required).
        """
        new_theme = self._tm.next_theme()
        self._settings.theme = new_theme
        self._settings.save()
        logger.info("Dark mode toggled -> %s", new_theme)
        self._rebuild_ui()

    # ══════════════════════════════════════════════════════════
    # LOAD FOLDER FLOW
    # ══════════════════════════════════════════════════════════

    def _load_folder(self, folder: str) -> None:
        """Kick off a background thread to load Excel files."""
        self._status_bar.set_status("Loading files…", "primary")
        self._status_bar.set_progress(0.0, "Starting…")
        self._cards["card_status"].set_value("Loading…")
        self.update_idletasks()

        def _thread() -> None:
            result = self._engine.load_folder(
                folder,
                progress_callback=lambda msg, frac: self.after(
                    0, lambda m=msg, f=frac: self._on_load_progress(m, f)
                ),
            )
            self.after(0, lambda r=result: self._on_load_complete(r, folder))

        threading.Thread(target=_thread, daemon=True).start()

    def _on_load_progress(self, message: str, fraction: float) -> None:
        """Update progress bar from the main thread."""
        self._status_bar.set_progress(fraction, message)
        self._status_bar.set_status(message, "primary")

    def _on_load_complete(self, result, folder: str) -> None:
        """Handle load completion on the main thread."""
        self._status_bar.set_progress(1.0 if result.success else 0.0, "")
        self._status_bar.reset_progress()

        if result.success:
            self._settings.last_folder = folder
            self._settings.save()
            self._folder_var.set(
                f"Folder : {folder}   |   Files : {result.file_count}   |   "
                f"Records : {result.record_count:,}"
            )
            self._cards["card_files"].set_value(str(result.file_count))
            self._cards["card_records"].set_value(f"{result.record_count:,}")
            self._cards["card_status"].set_value("Ready")
            self._status_bar.set_status(result.message, "success")

            if result.failed_files:
                detail = "\n".join(result.failed_files)
                InfoDialog(
                    self, self._tm,
                    "Load Warning",
                    f"{len(result.failed_files)} file(s) could not be read.\n"
                    "See logs/app.log for details.",
                )

            self._search_entry.focus_set()
            logger.info("Folder loaded: %s", folder)
        else:
            self._cards["card_status"].set_value("Error")
            self._show_error("Load Failed", result.message)

    # ══════════════════════════════════════════════════════════
    # SEARCH FLOW
    # ══════════════════════════════════════════════════════════

    def _do_search(self, do_number: str) -> None:
        """Search for a record and populate the panels."""
        self._status_bar.set_status(f"Searching: {do_number}…", "primary")
        self._cards["card_status"].set_value("Searching…")
        self.update_idletasks()

        result = self._engine.search(do_number)
        self._current_result = result

        if result.found:
            self._populate_panels(result)
            self._search_count += 1
            self._last_search = do_number
            self._cards["card_searches"].set_value(str(self._search_count))
            self._cards["card_last"].set_value(do_number)
            self._cards["card_status"].set_value("Found ✓")
            self._status_bar.set_status(
                f"Found: {result.customer_name} ({result.source_file})", "success"
            )
            self._history.add_entry(
                do_number,
                result.customer_name,
                result.sales_executive,
                result.source_file,
            )
            self._focus_search()
        else:
            self._cmd_clear()
            self._search_var.set(do_number)  # restore search term
            self._cards["card_status"].set_value("Not Found")
            self._status_bar.set_status(
                f"DO Number '{do_number}' not found.", "danger"
            )
            InfoDialog(self, self._tm, "Not Found",
                       f"DO Number '{do_number}' was not found\nin any loaded file.")
            self._focus_search()

    def _populate_panels(self, result: SearchResult) -> None:
        """
        Fill all three detail panels with formatted field values.

        Args:
            result: A successful SearchResult.
        """
        fields = result.fields

        # Battery row visibility
        is_battery = fields.get("_IS_BATTERY", "0") == "1"
        if "vehicle" in self._panels:
            self._panels["vehicle"].set_row_visible("BATTERY TYPE ROW", is_battery)

        # Populate every known panel
        for panel in self._panels.values():
            for key, value in fields.items():
                if key.startswith("_"):
                    continue
                panel.set_field(key, value)

    # ══════════════════════════════════════════════════════════
    # HISTORY DOUBLE-CLICK
    # ══════════════════════════════════════════════════════════

    def _on_history_double_click(self, do_number: str) -> None:
        """Reload a record from the history table."""
        self._search_var.set(do_number)
        self._do_search(do_number)

    # ══════════════════════════════════════════════════════════
    # SETTINGS APPLIED
    # ══════════════════════════════════════════════════════════

    def _on_settings_applied(self, new_settings: AppSettings) -> None:
        """Apply new settings from the Settings dialog, instantly."""
        old_theme = self._settings.theme
        self._settings = new_settings
        self._settings.save()

        if new_settings.theme != old_theme:
            self._tm.set_theme(new_settings.theme)
            self._rebuild_ui()

        logger.info("Settings applied: theme=%s", new_settings.theme)

    # ══════════════════════════════════════════════════════════
    # AUTO-LOAD
    # ══════════════════════════════════════════════════════════

    def _auto_load(self) -> None:
        """Silently load the last-used or fallback folder on startup."""
        folder = self._settings.last_folder
        if folder and os.path.isdir(folder):
            logger.info("Auto-loading last folder: %s", folder)
            self._load_folder(folder)
            return

        if os.path.isdir(DEFAULT_FALLBACK_FOLDER):
            logger.info("Auto-loading fallback folder: %s", DEFAULT_FALLBACK_FOLDER)
            self._load_folder(DEFAULT_FALLBACK_FOLDER)
            return

        self._status_bar.set_status("Ready — Load a folder to begin.", "text_muted")
        self._cards["card_status"].set_value("Ready")

    # ══════════════════════════════════════════════════════════
    # HELPERS
    # ══════════════════════════════════════════════════════════

    def _show_error(self, title: str, message: str) -> None:
        """Display an error dialog and log the error."""
        logger.error("%s: %s", title, message)
        ErrorDialog(self, self._tm, title, message)

    def _on_close(self) -> None:
        """Save settings and exit gracefully."""
        try:
            if not self.state() == "zoomed":
                self._settings.window_width = self.winfo_width()
                self._settings.window_height = self.winfo_height()
                self._settings.window_x = self.winfo_x()
                self._settings.window_y = self.winfo_y()
            self._settings.window_maximized = (self.state() == "zoomed")
            self._settings.save()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not save window state: %s", exc)
        logger.info("Application exiting.")
        self.destroy()


# ─────────────────────────────────────────────
# HELPER — separator
# ─────────────────────────────────────────────

def _sep(
    parent: ctk.CTkBaseClass,
    tm: ThemeManager,
    side: str = "left",
) -> None:
    """Insert a thin vertical separator line in the navbar."""
    ctk.CTkFrame(
        parent,
        width=1,
        height=30,
        fg_color=tm.c("text_dim"),
        corner_radius=0,
    ).pack(side=side, padx=5, pady=10)
