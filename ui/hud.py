"""
hud.py
Futuristic terminal HUD for JARVIS using the Rich library.

Layout
──────
┌─────────────── HEADER (time + title) ───────────────┐
│  Conversation feed          │  Status panel          │
│  (scrolling transcript)     │  (state + icon)        │
├─────────────────────────────┴────────────────────────┤
│  Audio Level visualizer bar                          │
└──────────────────────────────────────────────────────┘

Thread safety: all setters acquire a lock so the render thread
always sees a consistent snapshot.

Usage
─────
    from ui.hud import HUD
    hud = HUD()
    hud.start()                       # launch background refresh thread
    hud.update_status("listening")
    hud.add_message("user", "Hello")
    hud.add_message("jarvis", "Hi!")
    hud.set_audio_level(0.6)
    hud.stop()
"""
import threading
import time
from collections import deque
from datetime import datetime
from typing import Optional

from core.logger import get_logger

logger = get_logger(__name__)

try:
    from rich              import box
    from rich.console      import Console
    from rich.layout       import Layout
    from rich.live         import Live
    from rich.panel        import Panel
    from rich.table        import Table
    from rich.text         import Text
    _RICH = True
except ImportError:
    _RICH = False
    logger.warning("rich not installed — HUD disabled. Install: pip install rich")

# ── State colour palette ──────────────────────────────────────────────────────
_STATE_COLOR = {
    "idle":       "bright_cyan",
    "wake":       "bright_blue",
    "listening":  "bright_green",
    "processing": "bright_yellow",
    "speaking":   "bright_magenta",
    "error":      "bright_red",
}
_STATE_ICON = {
    "idle":       "😴",
    "wake":       "👋",
    "listening":  "🎤",
    "processing": "🧠",
    "speaking":   "🔊",
    "error":      "❌",
}


class HUD:
    """
    Thread-safe terminal HUD.

    Args:
        refresh_rate: Display refresh frequency in Hz (default 4).
        max_messages: Maximum messages kept in the conversation feed.
    """

    def __init__(self, refresh_rate: int = 4, max_messages: int = 20):
        self._state:        str   = "idle"
        self._audio_level:  float = 0.0        # 0.0 – 1.0
        self._messages:     deque = deque(maxlen=max_messages)
        self._refresh_rate: int   = refresh_rate
        self._lock          = threading.Lock()
        self._running:      bool  = False
        self._thread:       Optional[threading.Thread] = None

    # ── Public setters (thread-safe) ──────────────────────────────────────────
    def update_status(self, state: str):
        """Set the current JARVIS state (idle | wake | listening | processing | speaking | error)."""
        with self._lock:
            self._state = state

    def set_audio_level(self, level: float):
        """Set the audio bar level. `level` should be between 0.0 and 1.0."""
        with self._lock:
            self._audio_level = max(0.0, min(1.0, level))

    def add_message(self, role: str, text: str):
        """
        Add a message to the conversation feed.

        Args:
            role: "user" or "jarvis"
            text: The message content.
        """
        with self._lock:
            self._messages.append({
                "role": role,
                "text": text[:200],          # cap very long lines
                "time": datetime.now().strftime("%H:%M:%S"),
            })

    # ── Lifecycle ─────────────────────────────────────────────────────────────
    def start(self):
        """Launch the background refresh thread."""
        if not _RICH:
            logger.warning("HUD not started — rich library is missing.")
            return
        self._running = True
        self._thread  = threading.Thread(target=self._render_loop, daemon=True)
        self._thread.start()
        logger.info("HUD started.")

    def stop(self):
        """Signal the background thread to exit."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        logger.info("HUD stopped.")

    # ── Render loop ───────────────────────────────────────────────────────────
    def _render_loop(self):
        console = Console()
        interval = 1.0 / self._refresh_rate
        try:
            with Live(
                self._build_layout(),
                console=console,
                refresh_per_second=self._refresh_rate,
                screen=True,
            ) as live:
                while self._running:
                    live.update(self._build_layout())
                    time.sleep(interval)
        except Exception as e:
            logger.error("HUD render error: %s", e)
            self._running = False

    # ── Layout builders ───────────────────────────────────────────────────────
    def _build_layout(self) -> Layout:
        layout = Layout()
        layout.split_column(
            Layout(name="header",       size=3),
            Layout(name="body",         ratio=1),
            Layout(name="audio_footer", size=5),
        )
        layout["body"].split_row(
            Layout(name="conversation", ratio=3),
            Layout(name="status",       ratio=1),
        )
        layout["header"]       .update(self._render_header())
        layout["conversation"] .update(self._render_conversation())
        layout["status"]       .update(self._render_status())
        layout["audio_footer"] .update(self._render_audio())
        return layout

    def _render_header(self) -> Panel:
        now = datetime.now().strftime("%A  %d %B %Y  •  %H:%M:%S")
        t   = Text(justify="center")
        t.append("⚡ J.A.R.V.I.S ", style="bold bright_cyan")
        t.append("· Mark I  ·  ", style="dim cyan")
        t.append(now, style="dim white")
        return Panel(t, style="bright_cyan on black", box=box.DOUBLE_EDGE)

    def _render_conversation(self) -> Panel:
        with self._lock:
            msgs = list(self._messages)

        table = Table(show_header=False, box=None, padding=(0, 1), expand=True)
        table.add_column("time",  style="dim white",   width=10, no_wrap=True)
        table.add_column("role",  width=8,              no_wrap=True)
        table.add_column("text",  ratio=1)

        for msg in msgs[-14:]:
            if msg["role"] == "jarvis":
                role_txt = Text("JARVIS", style="bold bright_cyan")
            else:
                role_txt = Text("YOU",    style="bold bright_white")
            table.add_row(msg["time"], role_txt, msg["text"])

        return Panel(
            table,
            title="[bold cyan]Conversation[/bold cyan]",
            style="cyan on black",
            box=box.ROUNDED,
        )

    def _render_status(self) -> Panel:
        with self._lock:
            state = self._state

        color = _STATE_COLOR.get(state, "white")
        icon  = _STATE_ICON .get(state, "•")
        label = state.upper()

        body = Text(f"\n  {icon}\n\n  {label}\n", style=f"bold {color}", justify="center")
        return Panel(
            body,
            title="[bold cyan]Status[/bold cyan]",
            style="cyan on black",
            box=box.ROUNDED,
        )

    def _render_audio(self) -> Panel:
        with self._lock:
            level = self._audio_level

        bar_width = 44
        filled    = int(level * bar_width)
        bar       = "█" * filled + "░" * (bar_width - filled)
        pct       = int(level * 100)

        if level < 0.5:
            bar_color = "bright_green"
        elif level < 0.8:
            bar_color = "bright_yellow"
        else:
            bar_color = "bright_red"

        bar_txt = Text(justify="left")
        bar_txt.append(f"\n  🎙  Audio Level  ", style="dim white")
        bar_txt.append(f"[{bar}]", style=bar_color)
        bar_txt.append(f"  {pct:3d}%\n", style="dim white")

        return Panel(
            bar_txt,
            title="[bold cyan]Audio Visualizer[/bold cyan]",
            style="cyan on black",
            box=box.ROUNDED,
        )
