"""
logger.py
Centralised logging for JARVIS.
Uses Rich for coloured console output + a rotating file handler.
Import pattern:
    from core.logger import get_logger
    logger = get_logger(__name__)
"""
import logging
import os
from logging.handlers import RotatingFileHandler

try:
    from rich.logging import RichHandler
    _RICH_AVAILABLE = True
except ImportError:
    _RICH_AVAILABLE = False

LOG_DIR  = "logs"
LOG_FILE = os.path.join(LOG_DIR, "jarvis.log")


def get_logger(name: str = "jarvis") -> logging.Logger:
    """
    Return a named logger with:
      • console handler  (INFO+)  — Rich coloured or plain
      • file handler     (DEBUG+) — rotating, 2 MB, 3 backups
    Calling this multiple times with the same name is safe (idempotent).
    """
    logger = logging.getLogger(name)

    if logger.handlers:          # already configured — return as-is
        return logger

    logger.setLevel(logging.DEBUG)

    # ── Console handler ───────────────────────────────────────────────────────
    if _RICH_AVAILABLE:
        ch = RichHandler(
            rich_tracebacks=True,
            markup=True,
            show_time=True,
            show_path=False,
            level=logging.INFO,
        )
    else:
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )

    # ── File handler ──────────────────────────────────────────────────────────
    os.makedirs(LOG_DIR, exist_ok=True)
    fh = RotatingFileHandler(
        LOG_FILE,
        maxBytes=2 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)-8s] %(name)s — %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    logger.addHandler(ch)
    logger.addHandler(fh)
    return logger
