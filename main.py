"""
main.py
=======
Entry point for the DONSS application.

Usage:
    python main.py

PyInstaller:
    pyinstaller --onefile --windowed --name DONSS main.py
"""

from __future__ import annotations

import sys
import os

# ── Ensure the project root is on sys.path when running as a script ──
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from core.logger_setup import setup_logging

# Set up logging FIRST so every subsequent import can use the logger
setup_logging()

import logging

logger = logging.getLogger(__name__)


def main() -> None:
    """Bootstrap and run the DONSS application."""
    try:
        logger.info("Importing UI modules…")
        from ui.app_window import AppWindow

        logger.info("Starting main window…")
        app = AppWindow()
        app.mainloop()

    except ImportError as exc:
        logger.critical("Missing dependency: %s", exc)
        # Graceful console error if CTk is not installed
        print(
            f"\n[DONSS] ImportError: {exc}\n"
            "Please install requirements:\n"
            "    pip install -r requirements.txt\n"
        )
        sys.exit(1)

    except Exception as exc:  # noqa: BLE001
        logger.critical("Unhandled exception: %s", exc, exc_info=True)
        # Try to show a native error box as last resort
        try:
            import tkinter.messagebox as mb
            mb.showerror(
                "DONSS — Fatal Error",
                f"An unexpected error occurred:\n\n{exc}\n\n"
                "See logs/app.log for details.",
            )
        except Exception:  # noqa: BLE001
            print(f"[DONSS] Fatal: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
