# DONSS — DO Number Search System

> **Professional Edition v2.0.0** · Made with ❤️ by Abhishek Jha

A high-performance, production-ready Windows desktop application for searching and viewing DO Number records from Excel files — built with Python, CustomTkinter, and Pandas.

---

## ✨ Features

| Feature | Detail |
|---|---|
| 🚀 **High Performance** | Handles 500+ Excel files and 500,000+ rows via background threading |
| 🎨 **Premium Dark UI** | Windows 11-style interface with rounded corners and smooth animations |
| 🔍 **Instant Search** | Search by DO Number with Enter key or Ctrl+F focus shortcut |
| 📊 **Summary Cards** | Live counters for files, records, searches, and status |
| 🕘 **Search History** | Tabular history with double-click reload |
| 📤 **Export** | Export a single record or the entire dataset to Excel |
| 🌗 **Themes** | Dark, Light, and System themes with persistence |
| 💾 **Auto-Load** | Remembers last-used folder and reloads on startup |
| 📝 **Logging** | Rotating log file at `logs/app.log` |
| 🛡️ **Error Handling** | Never crashes — all errors shown as professional dialogs |

---

## 📦 Requirements

- **Python 3.13+**
- **Windows 10 / 11** (primary target; may work on macOS/Linux with minor adjustments)

### Python Packages

```
customtkinter>=5.2.2
pandas>=2.0.0
openpyxl>=3.1.0
```

---

## ⚡ Installation

```bash
# 1. Clone or download the project
git clone https://github.com/AbhishekJha3511/donss.git
cd donss

# 2. Create a virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt
```

---

## 🚀 Running

```bash
python main.py
```

### Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Enter` | Search DO Number |
| `Ctrl + F` | Focus search box |
| `Escape` | Exit application |

---

## 🏗️ Project Structure

```
donss/
├── main.py                  # Entry point
├── requirements.txt
├── donss.spec               # PyInstaller build spec
├── config.json              # Auto-generated settings file
│
├── core/
│   ├── __init__.py
│   ├── constants.py         # Column aliases, layouts, display names
│   ├── data_engine.py       # Business logic: load, search, export
│   ├── logger_setup.py      # Rotating file + console logging
│   └── settings.py          # JSON-backed persistent settings
│
├── ui/
│   ├── __init__.py
│   ├── app_window.py        # Main window, toolbar, panels assembly
│   ├── dialogs.py           # Settings, About, Error, Info dialogs
│   ├── history_table.py     # Treeview-based search history table
│   ├── theme.py             # ThemeManager — colour token resolution
│   └── widgets.py           # Reusable: SummaryCard, DetailPanel, FieldRow, StatusBar
│
├── utils/
│   ├── __init__.py
│   └── formatters.py        # Pure-function text formatters (dates, numbers, names)
│
└── logs/
    └── app.log              # Auto-created rotating log (max 5 MB × 3 backups)
```

---

## 📁 Excel File Requirements

Place all `.xlsx` / `.xls` files in a single folder and load it via **📂 Load**.

The application recognises a wide range of column header variations (see `core/constants.py` → `COLUMN_ALIASES`). Required column: **DONUMBER** (or any alias).

---

## 📸 Screenshots

> *(Add screenshots here after first run)*

| Dark Theme | Light Theme |
|---|---|
| ![Dark](docs/dark.png) | ![Light](docs/light.png) |

---

## 📦 Creating an EXE (PyInstaller)

```bash
pip install pyinstaller

# Using the included spec file (recommended)
pyinstaller donss.spec

# Or one-liner
pyinstaller --onefile --windowed --name DONSS main.py
```

The output EXE will be at `dist/DONSS.exe`.

> **Tip:** Add an icon by placing `assets/icon.ico` and uncommenting the `icon=` line in `donss.spec`.

---

## 🛠️ Troubleshooting

| Problem | Solution |
|---|---|
| `ModuleNotFoundError: customtkinter` | Run `pip install customtkinter` |
| App starts but no data appears | Check `logs/app.log` for column mapping errors |
| Excel file skipped on load | File may be open in Excel (locked). Close it and refresh. |
| `DONUMBER column not found` | Ensure at least one file has a DO Number column (see aliases in constants.py) |
| Slow load with many files | Normal for 500+ files; progress bar shows loading status |
| EXE crashes silently | Run `python main.py` first to see console errors |

---

## 📜 License

MIT — free to use and modify.

---

## 👤 Author

**Abhishek Jha** · [GitHub](https://github.com/AbhishekJha3511)
