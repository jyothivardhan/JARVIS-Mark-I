"""
system_tools.py
System-level tools: time, date, battery, CPU, RAM, OS info, open applications.

Optional dependency:  psutil  (pip install psutil)
  • get_battery(), get_cpu_usage(), get_memory_usage() need psutil.
  • All other methods work without it.
"""
import os
import platform
import subprocess
import webbrowser
from datetime import datetime

from core.logger import get_logger

logger = get_logger(__name__)

try:
    import psutil
    _PSUTIL = True
except ImportError:
    _PSUTIL = False
    logger.warning("psutil not installed — battery/CPU/RAM tools will be unavailable.")


class SystemTools:

    # ── Time & Date ───────────────────────────────────────────────────────────
    @staticmethod
    def get_time() -> str:
        return f"The current time is {datetime.now().strftime('%I:%M %p')}."

    @staticmethod
    def get_date() -> str:
        return f"Today is {datetime.now().strftime('%A, %d %B %Y')}."

    # ── OS / Hardware ─────────────────────────────────────────────────────────
    @staticmethod
    def get_system_info() -> str:
        return (
            f"Running {platform.system()} {platform.release()} "
            f"({platform.machine()})."
        )

    @staticmethod
    def get_battery() -> str:
        if not _PSUTIL:
            return "psutil is not installed — cannot check battery status."
        try:
            batt = psutil.sensors_battery()
            if batt is None:
                return "No battery sensor detected (this may be a desktop PC)."
            status = "charging" if batt.power_plugged else "discharging"
            return f"Battery is at {batt.percent:.0f}% and {status}."
        except Exception as e:
            logger.error("Battery check error: %s", e)
            return f"Could not read battery: {e}"

    @staticmethod
    def get_cpu_usage() -> str:
        if not _PSUTIL:
            return "psutil is not installed — cannot check CPU usage."
        try:
            usage = psutil.cpu_percent(interval=0.5)
            cores = psutil.cpu_count(logical=True)
            return f"CPU usage is {usage:.1f}% across {cores} logical cores."
        except Exception as e:
            logger.error("CPU check error: %s", e)
            return f"Could not read CPU usage: {e}"

    @staticmethod
    def get_memory_usage() -> str:
        if not _PSUTIL:
            return "psutil is not installed — cannot check RAM usage."
        try:
            vm   = psutil.virtual_memory()
            used  = vm.used  / (1024 ** 3)
            total = vm.total / (1024 ** 3)
            return (
                f"RAM: {used:.1f} GB used out of {total:.1f} GB "
                f"({vm.percent:.0f}% utilised)."
            )
        except Exception as e:
            logger.error("RAM check error: %s", e)
            return f"Could not read memory usage: {e}"

    # ── Applications ──────────────────────────────────────────────────────────
    # Maps common spoken names → executable / command
    _APP_MAP: dict[str, str] = {
        "notepad":      "notepad",
        "calculator":   "calc",
        "paint":        "mspaint",
        "task manager": "taskmgr",
        "cmd":          "cmd",
        "terminal":     "cmd",
        "explorer":     "explorer",
        "chrome":       "chrome",
        "firefox":      "firefox",
        "spotify":      "spotify",
        "vscode":       "code",
        "vs code":      "code",
        "word":         "winword",
        "excel":        "excel",
        "powerpoint":   "powerpnt",
    }

    def open_application(self, name: str) -> str:
        name_lower = name.lower().strip()

        if "browser" in name_lower:
            webbrowser.open("https://www.google.com")
            return "Opening your default browser."

        cmd = self._APP_MAP.get(name_lower)
        if cmd:
            try:
                subprocess.Popen(cmd, shell=True)
                return f"Opening {name}."
            except Exception as e:
                logger.error("open_application('%s'): %s", name, e)
                return f"Failed to open {name}: {e}"

        # Generic fallback — try to run the name as-is
        try:
            subprocess.Popen(name_lower, shell=True)
            return f"Attempting to open '{name}'."
        except Exception as e:
            return f"Could not open '{name}': {e}"

    @staticmethod
    def clear_screen():
        os.system("cls" if os.name == "nt" else "clear")
