"""
vision_tools.py
Vision and screen tools.

  capture_screenshot()   saves a PNG snapshot to screenshots/
  read_clipboard()       reads plain text from the clipboard

Optional dependencies:
  Pillow     (pip install Pillow)      — for screenshots
  pyperclip  (pip install pyperclip)  — for clipboard access
"""
import os
import datetime

from core.logger import get_logger

logger = get_logger(__name__)

try:
    from PIL import ImageGrab
    _PIL = True
except ImportError:
    _PIL = False
    logger.warning("Pillow not installed — screenshot tool will be unavailable.")

try:
    import pyperclip
    _PYPERCLIP = True
except ImportError:
    _PYPERCLIP = False
    logger.warning("pyperclip not installed — clipboard tool will be unavailable.")

_SCREENSHOT_DIR = "screenshots"
_CLIPBOARD_MAX  = 400  # truncate clipboard content after this many chars


class VisionTools:

    # ── Screenshot ────────────────────────────────────────────────────────────
    def capture_screenshot(self) -> str:
        """Take a full-screen screenshot and save it to the screenshots/ folder."""
        if not _PIL:
            return "Pillow is not installed — screenshot is unavailable."
        try:
            os.makedirs(_SCREENSHOT_DIR, exist_ok=True)
            ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(_SCREENSHOT_DIR, f"screenshot_{ts}.png")
            img  = ImageGrab.grab()
            img.save(path)
            logger.info("Screenshot saved: %s", path)
            return f"Screenshot saved to '{path}'."
        except Exception as e:
            logger.error("Screenshot error: %s", e)
            return f"Screenshot failed: {e}"

    # ── Clipboard ─────────────────────────────────────────────────────────────
    def read_clipboard(self) -> str:
        """Return the current clipboard text content (truncated if very long)."""
        if not _PYPERCLIP:
            return "pyperclip is not installed — clipboard access is unavailable."
        try:
            text = pyperclip.paste()
            if not text or not text.strip():
                return "The clipboard is currently empty."
            if len(text) > _CLIPBOARD_MAX:
                text = text[:_CLIPBOARD_MAX] + "…"
            return f"Clipboard contains: {text.strip()}"
        except Exception as e:
            logger.error("Clipboard read error: %s", e)
            return f"Could not read clipboard: {e}"
