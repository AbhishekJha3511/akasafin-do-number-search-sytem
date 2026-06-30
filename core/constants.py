"""
constants.py
============
Central configuration, column aliases, layout definitions,
and display name mappings for the DONSS application.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

# ─────────────────────────────────────────────
# APP META
# ─────────────────────────────────────────────
APP_NAME: str = "DONSS"
APP_VERSION: str = "2.0.0"
APP_AUTHOR: str = "Abhishek Jha"
APP_GITHUB: str = "https://github.com/AbhishekJha3511"
APP_DESCRIPTION: str = "DO Number Search System — Professional Edition"

WINDOW_WIDTH: int = 1600
WINDOW_HEIGHT: int = 900
WINDOW_MIN_WIDTH: int = 1200
WINDOW_MIN_HEIGHT: int = 700

LOG_FILE: str = "logs/app.log"
CONFIG_FILE: str = "config.json"
DEFAULT_FALLBACK_FOLDER: str = r"C:\Users\ACER\Desktop\ABHISHEKJHA\DOEXCELFILES"

# ─────────────────────────────────────────────
# THEME COLOURS
# ─────────────────────────────────────────────
DARK_COLORS: Dict[str, str] = {
    "bg":              "#0f172a",
    "surface":         "#1e293b",
    "surface2":        "#273548",
    "border":          "#334155",
    "primary":         "#3b82f6",
    "primary_hover":   "#2563eb",
    "success":         "#10b981",
    "success_hover":   "#059669",
    "warning":         "#f59e0b",
    "danger":          "#ef4444",
    "danger_hover":    "#dc2626",
    "text":            "#f1f5f9",
    "text_muted":      "#94a3b8",
    "text_dim":        "#64748b",
    "value_bg":        "#0f172a",
    "value_fg":        "#f1f5f9",
    "card_bg":         "#1e293b",
    "navbar_bg":       "#0d1829",
    "statusbar_bg":    "#0d1829",
    "table_header":    "#1e3a5f",
    "table_row_even":  "#1e293b",
    "table_row_odd":   "#182030",
    "table_select":    "#1e40af",
    "scrollbar":       "#334155",
}

LIGHT_COLORS: Dict[str, str] = {
    "bg":              "#f1f5f9",
    "surface":         "#ffffff",
    "surface2":        "#f8fafc",
    "border":          "#e2e8f0",
    "primary":         "#2563eb",
    "primary_hover":   "#1d4ed8",
    "success":         "#059669",
    "success_hover":   "#047857",
    "warning":         "#d97706",
    "danger":          "#dc2626",
    "danger_hover":    "#b91c1c",
    "text":            "#0f172a",
    "text_muted":      "#475569",
    "text_dim":        "#94a3b8",
    "value_bg":        "#f1f5f9",
    "value_fg":        "#0f172a",
    "card_bg":         "#ffffff",
    "navbar_bg":       "#003366",
    "statusbar_bg":    "#1e293b",
    "table_header":    "#dbeafe",
    "table_row_even":  "#ffffff",
    "table_row_odd":   "#f8fafc",
    "table_select":    "#bfdbfe",
    "scrollbar":       "#cbd5e1",
}

# ─────────────────────────────────────────────
# COLUMN ALIASES
# ─────────────────────────────────────────────
COLUMN_ALIASES: Dict[str, List[str]] = {
    "LEAD NO.": [
        "LEAD NO.", "LEAD NO", "LEAD", "LEAD ID", "LEADID", "LEADNO", "LEADNO."
    ],
    "DONUMBER": [
        "DONUMBER", "DO NUMBER", "DO NUMBER ", "DO_NUMBER"
    ],
    "SALES EXECUTIVE": [
        "SALES EXECUTIVE", "SALESEXECUTIVE", "SALES_EXECUTIVE"
    ],
    "CUSTOMER NAME": [
        "CUSTOMER NAME", "CUSTOMERNAME", "CUST NAME"
    ],
    "CUSTOMER SURNAME": [
        "CUSTOMERSURNAME", "CUSTOMER SURNAME", "SURNAME"
    ],
    "CUSTOMER'S FATHER NAME": [
        "CUSTOMER'S FATHER NAME", "CUSTOMER'SFATHERNAME",
        "CUSTOMERSFATHERNAME", "CUSTOMERS FATHER NAME"
    ],
    "Dealer ship Name": [
        "Dealer ship Name", "DEALERSHIPNAME", "DEALERSHIP NAME",
        "DEALER SHIP NAME", "DEALERNAME", "DEALER NAME", "DealershipName"
    ],
    "PRODUCT":  ["PRODUCT"],
    "MODEL":    ["MODEL", "Model"],
    "Vehicle Catogery/battery type": [
        "Vehicle Catogery/battery type",
        "VEHICLECATOGERY/BATTERYTYPE", "VehicleCatogery/batterytype",
        "VEHICLECATOGERY", "VehicleCatogery", "VEHICLE CATOGERY",
        "VEHICLECATEGORY",
        "BATTERYTYPE(AKASACLEANENERGYLITHIUM/OTHERLITHIUM)",
        'BATTERYTYPE(AKASACLEANENERGYLITHIUM/OTHERLITHIUM)"',
        'BATTERY TYPE(AKASA CLEAN ENERGY LITHIUM/OTHER LITHIUM)"',
    ],
    "Vehicle cost":   ["Vehicle cost", "Vehiclecost", "VEHICLECOST", "VEHICLE COST"],
    "DOWN PAYMENT":   ["DOWN PAYMENT", "DOWNPAYMENT", "DOWN_PAYMENT"],
    "LOAN AMOUNT":    ["LOAN AMOUNT", "LOANAMOUNT", "Loanamount", "LOAN_AMOUNT"],
    "File charge":    ["File charge", "Filecharge", "FILECHARGE", "FILE CHARGE"],
    "Emi":            ["Emi", "EMI"],
    "TENURE":         ["TENURE"],
    "ADVANCE EMI":    ["ADVANCE EMI", "ADVANCEEMI", "ADVANCE_EMI"],
    "DISBURSEMENT AMOUNT": [
        "DISBURSEMENT AMOUNT", "DISBURSEMENTAMOUNT",
        "DISBURSMENT AMOUNT", "DISBURSMENT AMOUNT ", "DISBURSEMENT_AMOUNT"
    ],
    "NEFT DATE":  ["NEFT DATE", "NEFTDATE", "NEFT_DATE"],
    "DUE DATE":   ["DUE DATE", "DUEDATE", "DUE_DATE"],
    "ENACH/CHQ":  ["ENACH/CHQ", "ENACH", "CHQ"],
    "OEM MANUFECTURER'S NAME": [
        "OEM MANUFECTURER'S NAME", "OEMMANUFECTURER'SNAME",
        "OEM MANUFACTURER NAME", "OEM MANUFACTURER NAME ", "OEMMANUFACTURERNAME"
    ],
    "Engine_no":  ["Engine_no", "ENGINE NO", "ENGINE_NO", "ENGINENO", "Engine No"],
    "CHASSISNO":  ["CHASSISNO", "CHASSIS NO", "CHASSIS_NO", "ChassisNo"],
}

# ─────────────────────────────────────────────
# DISPLAY NAMES
# ─────────────────────────────────────────────
DISPLAY_NAMES: Dict[str, str] = {
    "LEAD NO.":                      "Lead No.",
    "DONUMBER":                      "DO Number",
    "DONUMBER_COPY":                 "DO Number",
    "SALES EXECUTIVE":               "Sales Executive",
    "CUSTOMER NAME":                 "Customer Name",
    "CUSTOMER FULL NAME":            "Customer Name",
    "CUSTOMER SURNAME":              "Customer Surname",
    "CUSTOMER'S FATHER NAME":        "Father's Name",
    "Dealer ship Name":              "Dealer Ship Name",
    "PRODUCT":                       "Product",
    "MODEL":                         "Model",
    "BATTERY TYPE ROW":              "Battery Type",
    "Vehicle Catogery/battery type": "Vehicle Category",
    "Vehicle cost":                  "Vehicle Cost",
    "DOWN PAYMENT":                  "Down Payment",
    "LOAN AMOUNT":                   "Loan Amount",
    "LOAN AMOUNT WORDS":             "Loan In Words",
    "File charge":                   "File Charge",
    "Emi":                           "EMI",
    "TENURE":                        "Tenure",
    "ADVANCE EMI":                   "Advance EMI",
    "DISBURSEMENT AMOUNT":           "Disbursement Amount",
    "NEFT DATE":                     "NEFT Date",
    "DUE DATE":                      "Due Date",
    "ENACH/CHQ":                     "ENACH / CHQ",
    "OEM MANUFECTURER'S NAME":       "OEM Manufacturer",
    "Engine_no":                     "Engine No.",
    "CHASSISNO":                     "Chassis No.",
}

# ─────────────────────────────────────────────
# PANEL LAYOUTS
# ─────────────────────────────────────────────
# Each entry: ("single", field) | ("pair", field1, field2)
LEFT_LAYOUT: List[Tuple] = [
    ("pair",   "LEAD NO.",            "DONUMBER"),
    ("single", "DUE DATE"),
    ("single", "Vehicle cost"),
    ("single", "DOWN PAYMENT"),
    ("pair",   "Emi",                 "TENURE"),
    ("single", "ADVANCE EMI"),
    ("single", "File charge"),
    ("single", "LOAN AMOUNT"),
    ("single", "LOAN AMOUNT WORDS"),
    ("single", "DISBURSEMENT AMOUNT"),
    ("single", "ENACH/CHQ"),
]

CUSTOMER_LAYOUT: List[Tuple] = [
    ("single", "NEFT DATE"),
    ("single", "DONUMBER_COPY"),
    ("single", "SALES EXECUTIVE"),
    ("single", "Dealer ship Name"),
    ("single", "CUSTOMER FULL NAME"),
    ("single", "CUSTOMER'S FATHER NAME"),
]

VEHICLE_LAYOUT: List[Tuple] = [
    ("single", "PRODUCT"),
    ("single", "MODEL"),
    ("single", "BATTERY TYPE ROW"),
    ("single", "Engine_no"),
    ("single", "CHASSISNO"),
    ("single", "Vehicle Catogery/battery type"),
    ("single", "OEM MANUFECTURER'S NAME"),
]

# Fields that need date formatting
DATE_FIELDS: set = {"NEFT DATE", "DUE DATE"}

# Fields that get title-case formatting
NAME_FIELDS: set = {
    "SALES EXECUTIVE", "Dealer ship Name",
    "OEM MANUFECTURER'S NAME", "Vehicle Catogery/battery type"
}

# All raw column names to fetch from DataFrame
def _raw_fields(layout: List[Tuple]) -> List[str]:
    out: List[str] = []
    for entry in layout:
        for key in entry[1:]:
            if key not in ("CUSTOMER FULL NAME", "BATTERY TYPE ROW",
                           "LOAN AMOUNT WORDS", "DONUMBER_COPY"):
                out.append(key)
    return list(dict.fromkeys(out))


ALL_FETCH_FIELDS: List[str] = list(dict.fromkeys(
    ["CUSTOMER NAME", "CUSTOMER SURNAME"]
    + _raw_fields(LEFT_LAYOUT)
    + _raw_fields(CUSTOMER_LAYOUT)
    + _raw_fields(VEHICLE_LAYOUT)
))

# History table columns
HISTORY_COLUMNS: Tuple[str, ...] = (
    "Time", "DO Number", "Customer Name", "Sales Executive", "Source File"
)
