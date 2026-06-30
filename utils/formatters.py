"""
formatters.py
=============
Pure-function text formatters used when displaying field values.
No UI dependencies — fully unit-testable.
"""

from __future__ import annotations

import re
from typing import Any, Optional

import pandas as pd


def clean_val(value: Any) -> str:
    """
    Safely convert any cell value to a clean string.

    - Returns empty string for None, NaN, NaT, 'nan', 'none', '<na>'
    - Strips leading/trailing whitespace

    Args:
        value: Raw cell value from a DataFrame.

    Returns:
        Cleaned string representation, or empty string.
    """
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:  # noqa: BLE001
        pass
    s = str(value).strip()
    return "" if s.lower() in ("nan", "none", "nat", "<na>", "nat") else s


def to_title_case(value: str) -> str:
    """
    Convert a string to title case, capitalising every word.

    Args:
        value: Input string.

    Returns:
        Title-cased string.
    """
    if not value:
        return ""
    return " ".join(word.capitalize() for word in value.split())


def format_father_name(value: str) -> str:
    """
    Normalise father's name — collapse whitespace, then title-case.

    Args:
        value: Raw father name string.

    Returns:
        Formatted name.
    """
    if not value:
        return ""
    return to_title_case(" ".join(value.split()))


def format_date(value: Any) -> str:
    """
    Parse any date-like value and return "DD/MM/YYYY (MonthName)".

    Args:
        value: Date string, datetime object, or pandas Timestamp.

    Returns:
        Formatted date string, or raw str(value) on failure.
    """
    try:
        if pd.isna(value):
            return ""
    except Exception:  # noqa: BLE001
        pass
    try:
        dt = pd.to_datetime(value)
        return dt.strftime("%d/%m/%Y") + f" ({dt.strftime('%B')})"
    except Exception:  # noqa: BLE001
        return str(value)


def round_disbursement(value: str) -> str:
    """
    Round a disbursement amount to the nearest integer and format
    it in Indian numbering style (e.g. 1,23,456).

    Args:
        value: Numeric string.

    Returns:
        Indian-formatted number string, or the original on failure.
    """
    if not value:
        return ""
    try:
        rounded = round(float(value))
        s = str(rounded)
        if len(s) <= 3:
            return s
        last3 = s[-3:]
        rest = s[:-3]
        groups: list[str] = []
        while len(rest) > 2:
            groups.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            groups.insert(0, rest)
        return ",".join(groups) + "," + last3
    except (ValueError, TypeError):
        return value


def number_to_words(amount: str) -> str:
    """
    Convert a numeric amount to Indian English words with "Only" suffix.

    Handles Crore, Lakh, Thousand, and Hundred.

    Args:
        amount: Numeric string (may be float-like).

    Returns:
        Human-readable word representation, or empty string on failure.
    """
    if not amount:
        return ""
    try:
        n = int(round(float(amount)))
    except (ValueError, TypeError):
        return ""

    if n == 0:
        return "Zero Only"

    ones = [
        "", "One", "Two", "Three", "Four", "Five", "Six", "Seven",
        "Eight", "Nine", "Ten", "Eleven", "Twelve", "Thirteen",
        "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen",
    ]
    tens_words = [
        "", "", "Twenty", "Thirty", "Forty", "Fifty",
        "Sixty", "Seventy", "Eighty", "Ninety",
    ]

    def _two(num: int) -> str:
        if num < 20:
            return ones[num]
        tail = (" " + ones[num % 10]) if num % 10 else ""
        return (tens_words[num // 10] + tail).strip()

    def _three(num: int) -> str:
        if num >= 100:
            remainder = _two(num % 100)
            return ones[num // 100] + " Hundred" + ((" " + remainder) if remainder else "")
        return _two(num)

    parts: list[str] = []
    crore = n // 10_000_000;  n %= 10_000_000   # noqa: E702
    lakh  = n // 100_000;     n %= 100_000       # noqa: E702
    thou  = n // 1_000;       n %= 1_000         # noqa: E702
    hund  = n

    if crore:
        parts.append(_three(crore) + " Crore")
    if lakh:
        parts.append(_three(lakh) + " Lakh")
    if thou:
        parts.append(_three(thou) + " Thousand")
    if hund:
        parts.append(_three(hund))

    return " ".join(parts).strip() + " Only"


def group_string(value: str, group_size: int) -> str:
    """
    Insert a space every *group_size* characters, grouping from the left.

    Used to make long alphanumeric codes (engine numbers, chassis
    numbers) easier to read at a glance.

    Example::

        group_string("MD626FK52R1H02345", 3)
        # -> "MD6 26F K52 R1H 023 45"

        group_string("MA3ERLF1S00123456", 4)
        # -> "MA3E RLF1 S001 2345 6"

    Args:
        value:      The raw alphanumeric string (no internal spaces).
        group_size: Number of characters per group.

    Returns:
        The grouped string with single spaces between groups, or the
        original (cleaned) value if it's empty or group_size <= 0.
    """
    if not value or group_size <= 0:
        return value
    # Strip any existing whitespace so grouping is consistent
    compact = re.sub(r"\s+", "", value)
    groups = [compact[i:i + group_size] for i in range(0, len(compact), group_size)]
    return " ".join(groups)


def format_engine_no(value: str) -> str:
    """
    Format an engine number with 3-character grouping for readability.

    Args:
        value: Raw engine number string.

    Returns:
        Grouped engine number (e.g. "MD6 26F K52 R1H 023 45").
    """
    return group_string(value, 3)


def format_chassis_no(value: str) -> str:
    """
    Format a chassis number with 4-character grouping for readability.

    Args:
        value: Raw chassis number string.

    Returns:
        Grouped chassis number (e.g. "MA3E RLF1 S001 2345 6").
    """
    return group_string(value, 4)
