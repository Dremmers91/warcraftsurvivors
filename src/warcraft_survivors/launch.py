"""Release entry point with user-data logging and actionable fatal error reporting."""

from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def log_directory() -> Path:
    # QA's private save override also isolates its logs from the ordinary profile.
    if "--save-dir" in sys.argv:
        index = sys.argv.index("--save-dir")
        if index + 1 < len(sys.argv):
            return Path(sys.argv[index + 1]) / "logs"
    return (
        Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
        / "WarcraftSurvivors/logs"
    )


def main() -> None:
    log_path = log_directory() / "game.log"
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(log_path, maxBytes=512_000, backupCount=2, encoding="utf-8")
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
            handlers=[handler],
            force=True,
        )
    except OSError:
        logging.basicConfig(level=logging.ERROR)
    logger = logging.getLogger(__name__)
    logger.info("Starting Warcraft Survivors; frozen=%s", getattr(sys, "frozen", False))
    try:
        from .app import main as run

        run()
    except Exception:
        logger.exception("Fatal application error")
        message = (
            "Warcraft Survivors could not continue. Extract the entire release folder and try again. "
            "If the problem remains, include this log when reporting it:\n" + str(log_path)
        )
        if (
            getattr(sys, "frozen", False)
            and sys.platform == "win32"
            and "--smoke-test" not in sys.argv
        ):
            import ctypes

            ctypes.windll.user32.MessageBoxW(None, message, "Warcraft Survivors", 0x10)
        elif sys.stderr:
            print(message, file=sys.stderr)
        raise SystemExit(1) from None
    logger.info("Application closed normally")
