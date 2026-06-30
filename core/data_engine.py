"""
data_engine.py
==============
Business-logic layer: Excel loading, column normalisation,
searching, and export. Completely decoupled from the UI.
"""

from __future__ import annotations

import difflib
import logging
import os
import re
import warnings
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple

import pandas as pd

from core.constants import (
    ALL_FETCH_FIELDS,
    COLUMN_ALIASES,
    DATE_FIELDS,
    NAME_FIELDS,
)
from utils.formatters import (
    clean_val,
    format_chassis_no,
    format_date,
    format_engine_no,
    format_father_name,
    number_to_words,
    round_disbursement,
    to_title_case,
)

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# COLUMN ALIAS LOOKUP
# ─────────────────────────────────────────────

def _norm(text: str) -> str:
    """Strip whitespace and uppercase for alias matching."""
    return re.sub(r"\s+", "", str(text)).upper().strip()


# Build a flat lookup: normalised_alias → canonical column name
_ALIAS_LOOKUP: Dict[str, str] = {}
for _canonical, _aliases in COLUMN_ALIASES.items():
    for _alias in _aliases:
        _ALIAS_LOOKUP[_norm(_alias)] = _canonical
    _ALIAS_LOOKUP[_norm(_canonical)] = _canonical


def _map_col(raw: str) -> str:
    """
    Map a raw column header to its canonical name.
    Uses exact match first, then fuzzy matching (cutoff=0.85).
    """
    key = _norm(raw)
    if key in _ALIAS_LOOKUP:
        return _ALIAS_LOOKUP[key]
    matches = difflib.get_close_matches(key, _ALIAS_LOOKUP.keys(), n=1, cutoff=0.85)
    return _ALIAS_LOOKUP[matches[0]] if matches else raw


def normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rename DataFrame columns to canonical names using alias mapping.
    Duplicate canonical columns are suffixed _DUP_n and then dropped.

    Args:
        df: Raw DataFrame with arbitrary column names.

    Returns:
        DataFrame with normalised column names.
    """
    new_names = [_map_col(c) for c in df.columns]
    seen: Dict[str, int] = {}
    final: List[str] = []
    for name in new_names:
        if name not in seen:
            seen[name] = 0
            final.append(name)
        else:
            seen[name] += 1
            final.append(f"_DUP_{name}_{seen[name]}")
    df.columns = final
    dup_cols = [c for c in df.columns if c.startswith("_DUP_")]
    df.drop(columns=dup_cols, inplace=True)
    return df


# ─────────────────────────────────────────────
# LOAD RESULT DATACLASS
# ─────────────────────────────────────────────

@dataclass
class LoadResult:
    """Result of a folder-load operation."""
    success: bool
    file_count: int = 0
    record_count: int = 0
    failed_files: List[str] = field(default_factory=list)
    message: str = ""


# ─────────────────────────────────────────────
# SEARCH RESULT DATACLASS
# ─────────────────────────────────────────────

@dataclass
class SearchResult:
    """Result of a single DO Number search."""
    found: bool
    do_number: str = ""
    fields: Dict[str, str] = field(default_factory=dict)
    source_file: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    customer_name: str = ""
    sales_executive: str = ""


# ─────────────────────────────────────────────
# DATA ENGINE
# ─────────────────────────────────────────────

class DataEngine:
    """
    Core data management class.

    Responsibilities:
    - Load and merge Excel files from a folder
    - Normalise column headers
    - Search records by DO Number
    - Format field values for display
    - Export records to Excel
    """

    def __init__(self) -> None:
        self._df: Optional[pd.DataFrame] = None
        self._folder: str = ""
        self._file_count: int = 0
        self._record_count: int = 0
        logger.info("DataEngine initialised")

    # ── Public properties ──────────────────────────────────────

    @property
    def is_loaded(self) -> bool:
        """True if a dataset is currently loaded."""
        return self._df is not None and not self._df.empty

    @property
    def file_count(self) -> int:
        return self._file_count

    @property
    def record_count(self) -> int:
        return self._record_count

    @property
    def folder(self) -> str:
        return self._folder

    # ── Loading ───────────────────────────────────────────────

    def load_folder(
        self,
        folder_path: str,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> LoadResult:
        """
        Load all .xlsx / .xls files from *folder_path* into a single DataFrame.

        Args:
            folder_path:       Absolute path to the folder.
            progress_callback: Optional callable(message, fraction 0..1).

        Returns:
            LoadResult with success flag and statistics.
        """
        logger.info("Loading folder: %s", folder_path)

        def _progress(msg: str, frac: float) -> None:
            if progress_callback:
                progress_callback(msg, frac)

        # ── Discover files ─────────────────────────────────────
        if not os.path.isdir(folder_path):
            msg = f"Folder not found: {folder_path}"
            logger.error(msg)
            return LoadResult(success=False, message=msg)

        excel_files = [
            os.path.join(folder_path, f)
            for f in sorted(os.listdir(folder_path))
            if f.lower().endswith((".xlsx", ".xls"))
            and not f.startswith("~$")  # skip temp lock files
        ]

        if not excel_files:
            msg = "No Excel files found in the selected folder."
            logger.warning(msg)
            return LoadResult(success=False, message=msg)

        _progress("Discovering files…", 0.05)
        total = len(excel_files)
        logger.info("Found %d Excel file(s)", total)

        # ── Read each file ─────────────────────────────────────
        frames: List[pd.DataFrame] = []
        failed: List[str] = []

        for idx, fp in enumerate(excel_files):
            fname = os.path.basename(fp)
            _progress(f"Reading: {fname}", 0.05 + 0.80 * (idx / total))
            try:
                raw = pd.read_excel(fp, dtype=str)
                raw.dropna(how="all", inplace=True)
                raw.dropna(axis=1, how="all", inplace=True)
                raw = normalise_columns(raw)
                raw["_SOURCE_FILE"] = fname
                frames.append(raw)
                logger.debug("Loaded %s (%d rows)", fname, len(raw))
            except PermissionError:
                msg = f"{fname}: Permission denied — file may be open in Excel."
                failed.append(msg)
                logger.warning(msg)
            except Exception as exc:  # noqa: BLE001
                msg = f"{fname}: {exc}"
                failed.append(msg)
                logger.error("Failed to read %s — %s", fname, exc)

        if not frames:
            msg = "Could not load any Excel file from the folder."
            logger.error(msg)
            return LoadResult(success=False, failed_files=failed, message=msg)

        # ── Merge ─────────────────────────────────────────────
        _progress("Merging data…", 0.87)
        merged = pd.concat(frames, ignore_index=True, sort=False)

        if "DONUMBER" not in merged.columns:
            msg = "DONUMBER column not found in any loaded file."
            logger.error(msg)
            return LoadResult(success=False, failed_files=failed, message=msg)

        # Build a fast search key
        merged["_DO_SEARCH"] = (
            merged["DONUMBER"].fillna("").astype(str)
            .str.strip().str.upper()
            .str.replace(r"\s+", "", regex=True)
        )

        self._df = merged
        self._folder = folder_path
        self._file_count = len(frames)
        self._record_count = len(merged)

        _progress("Completed", 1.0)
        logger.info(
            "Load complete — %d file(s), %d records, %d skipped",
            self._file_count, self._record_count, len(failed),
        )

        summary = (
            f"Loaded {self._file_count} file(s) with "
            f"{self._record_count:,} records."
        )
        if failed:
            summary += f"  ({len(failed)} skipped)"

        return LoadResult(
            success=True,
            file_count=self._file_count,
            record_count=self._record_count,
            failed_files=failed,
            message=summary,
        )

    # ── Searching ─────────────────────────────────────────────

    def search(self, do_number: str) -> SearchResult:
        """
        Search for a record by DO Number.

        Args:
            do_number: Raw DO Number string (case/whitespace insensitive).

        Returns:
            SearchResult with formatted fields if found.
        """
        if not self.is_loaded:
            return SearchResult(found=False, do_number=do_number,
                                fields={}, source_file="",
                                customer_name="", sales_executive="")

        query = re.sub(r"\s+", "", do_number.strip().upper())
        logger.info("Searching DO Number: %s", query)

        matches = self._df[self._df["_DO_SEARCH"] == query]
        if matches.empty:
            logger.info("Not found: %s", query)
            return SearchResult(found=False, do_number=do_number)

        row = matches.iloc[0]
        formatted = self._format_row(row)
        source = clean_val(row.get("_SOURCE_FILE", ""))
        customer = formatted.get("CUSTOMER FULL NAME", "")
        sales_exec = formatted.get("SALES EXECUTIVE", "")

        logger.info("Found DO %s — customer: %s", query, customer)
        return SearchResult(
            found=True,
            do_number=do_number,
            fields=formatted,
            source_file=source,
            customer_name=customer,
            sales_executive=sales_exec,
        )

    def _format_row(self, row: pd.Series) -> Dict[str, str]:
        """
        Apply all field-specific formatters to a DataFrame row.

        Args:
            row: A single row from the loaded DataFrame.

        Returns:
            Dict mapping field keys to formatted display strings.
        """
        result: Dict[str, str] = {}

        # Customer full name
        first = to_title_case(clean_val(row.get("CUSTOMER NAME", "")))
        last = to_title_case(clean_val(row.get("CUSTOMER SURNAME", "")))
        result["CUSTOMER FULL NAME"] = (first + " " + last).strip()

        # Battery type (conditional)
        model_raw = clean_val(row.get("MODEL", "")).upper()
        is_battery = "BATTERY" in model_raw
        if is_battery:
            bat = to_title_case(clean_val(row.get("Vehicle Catogery/battery type", "")))
            result["BATTERY TYPE ROW"] = bat.upper() if bat else ""
        result["_IS_BATTERY"] = "1" if is_battery else "0"

        # All standard fields
        for field_key in ALL_FETCH_FIELDS:
            if field_key in ("CUSTOMER NAME", "CUSTOMER SURNAME"):
                continue
            val = clean_val(row.get(field_key, ""))
            val = self._apply_formatter(field_key, val)
            result[field_key] = val

        # Loan in words (derived)
        loan_raw = clean_val(row.get("LOAN AMOUNT", ""))
        result["LOAN AMOUNT WORDS"] = number_to_words(loan_raw)

        # DO Number copy for customer panel
        result["DONUMBER_COPY"] = clean_val(row.get("DONUMBER", "")).upper()

        return result

    @staticmethod
    def _apply_formatter(field_key: str, val: str) -> str:
        """
        Route a field value through the correct formatter.

        Args:
            field_key: Canonical column name.
            val:       Raw string value.

        Returns:
            Formatted string value.
        """
        if not val:
            return ""

        if field_key == "CUSTOMER'S FATHER NAME":
            return format_father_name(val)
        if field_key == "DISBURSEMENT AMOUNT":
            return round_disbursement(val)
        if field_key in DATE_FIELDS:
            return format_date(val)
        if field_key == "Engine_no":
            return format_engine_no(val.upper())
        if field_key == "CHASSISNO":
            return format_chassis_no(val.upper())
        if field_key == "DONUMBER":
            return val.upper()
        if field_key == "ENACH/CHQ":
            return val.upper()
        if field_key in NAME_FIELDS:
            return to_title_case(val)
        if field_key == "MODEL":
            return val.upper()
        return to_title_case(val)

    # ── Export ────────────────────────────────────────────────

    def export_record(self, result: SearchResult, output_path: str) -> bool:
        """
        Export a single SearchResult to an Excel file.

        Args:
            result:      The SearchResult to export.
            output_path: Full path for the output .xlsx file.

        Returns:
            True on success, False on failure.
        """
        try:
            rows = [
                {"Field": DISPLAY_NAME_FOR.get(k, k), "Value": v}
                for k, v in result.fields.items()
                if not k.startswith("_")
            ]
            df_out = pd.DataFrame(rows)
            df_out.to_excel(output_path, index=False, engine="openpyxl")
            logger.info("Exported record %s → %s", result.do_number, output_path)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("Export failed: %s", exc)
            return False

    def export_all(self, output_path: str) -> bool:
        """
        Export the complete loaded DataFrame to an Excel file.

        Args:
            output_path: Full path for the output .xlsx file.

        Returns:
            True on success, False on failure.
        """
        if not self.is_loaded:
            logger.warning("export_all called with no data loaded")
            return False
        try:
            export_df = self._df.drop(
                columns=[c for c in self._df.columns if c.startswith("_")],
                errors="ignore",
            )
            export_df.to_excel(output_path, index=False, engine="openpyxl")
            logger.info("Exported all data → %s (%d rows)", output_path, len(export_df))
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("Export all failed: %s", exc)
            return False


# Lazy import to avoid circular – only used by export_record
from core.constants import DISPLAY_NAMES as DISPLAY_NAME_FOR  # noqa: E402
