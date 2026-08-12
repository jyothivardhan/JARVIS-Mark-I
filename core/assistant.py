"""
assistant.py
Top-level JARVIS orchestrator.

Full pipeline (voice mode):
  Wake Word  →  VAD Record  →  Whisper STT  →  CommandRouter/FunctionAgent
             →  TTS Speaker  →  HUD update

Keyboard mode skips wake word + STT and reads commands from stdin.
"""
from config.settings import ASSISTANT_NAME, VERSION, UI_ENABLED, HUD_REFRESH_RATE
from core.llm        import LLM
from core.logger     import get_logger
from commands.router import CommandRouter
from memory.memory   import Memory
from memory.vector_memory import VectorMemory
from speech.speech_manager import SpeechManager
from speech.speaker  import Speaker

logger = get_logger(__name__)


class Assistant:

    def __init__(self):
        self.name = ASSISTANT_NAME
        logger.info("Initialising %s v%s…", self.name, VERSION)

        # Core components
        self.llm           = LLM()
        self.memory        = Memory()
        self.vector_memory = VectorMemory()
        self.router        = CommandRouter(self.llm, self.memory, self.vector_memory)
        self.speech        = SpeechManager()
        self.speaker       = Speaker()

        # Optional HUD
        self.hud = None
        if UI_ENABLED:
            self._init_hud()

    # ── HUD ───────────────────────────────────────────────────────────────────
    def _init_hud(self):
        try:
            from ui.hud import HUD
            self.hud = HUD(refresh_rate=HUD_REFRESH_RATE)
            self.hud.start()
            logger.info("HUD started.")
        except Exception as e:
            logger.warning("HUD failed to start: %s", e)
            self.hud = None

    def _set_status(self, state: str):
        if self.hud:
            self.hud.update_status(state)

    def _log_msg(self, role: str, text: str):
        if self.hud:
            self.hud.add_message(role, text)

    # ── Startup banner ────────────────────────────────────────────────────────
    def start(self):
        self._banner()

        if not self.llm.check_connection():
            logger.error("Ollama is not running.")
            print("\n[ERROR] Ollama is not running. Please start Ollama and retry.\n")
            return

        logger.info("Connected to model: %s", self.llm.get_model())
        print(f"  Model : {self.llm.get_model()}")
        print(f"  Type 'help' for available commands.\n")
        self._set_status("idle")

        self._mode_select_loop()

    def _banner(self):
        width = 50
        print("\n" + "═" * width)
        print(f"{'  ⚡  ' + self.name + '  —  Mark I':^{width}}")
        print(f"{'v' + VERSION:^{width}}")
        print("═" * width + "\n")

    # ── Mode selector ─────────────────────────────────────────────────────────
    def _mode_select_loop(self):
        print("  (v) Voice mode    (k) Keyboard mode    (q) Quit\n")
        while True:
            try:
                choice = input("  Mode > ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                self._shutdown()
                return

            if choice in ("q", "quit", "exit", "sleep"):
                self._shutdown()
                return
            elif choice == "v":
                self._voice_loop()
            else:
                self._keyboard_loop()

    # ── Voice loop ────────────────────────────────────────────────────────────
    def _voice_loop(self):
        """Continuous voice mode: detect wake word → VAD record → respond."""
        print("\n  [Voice mode] Say the wake word to activate. Ctrl+C to exit.\n")
        self._set_status("wake")

        while True:
            try:
                # 1. Wait for wake word
                self.speech.listen_for_wake_word()
                self._set_status("listening")

                # 2. Record utterance (VAD-gated)
                command = self.speech.listen(use_vad=True)
                if not command:
                    self._set_status("wake")
                    continue

                print(f"\n  You    > {command}")
                self._log_msg("user", command)

                if command.lower().strip() in ("sleep", "goodbye", "bye", "exit", "quit"):
                    self._shutdown()
                    break

                # 3. Route → generate response
                self._set_status("processing")
                response = self._safe_execute(command)

                if response:
                    print(f"  JARVIS > {response}\n")
                    self._log_msg("jarvis", response)

                    # 4. Speak
                    self._set_status("speaking")
                    self.speaker.speak(response)

                self._set_status("wake")

            except KeyboardInterrupt:
                print("\n  [Voice mode exited]")
                break
            except Exception as e:
                logger.error("Voice loop error: %s", e)
                self._set_status("error")

    # ── Keyboard loop ─────────────────────────────────────────────────────────
    def _keyboard_loop(self):
        """Single-session keyboard interaction."""
        print("\n  [Keyboard mode] Type 'back' to return to mode select.\n")

        while True:
            try:
                command = input("  You    > ").strip()
            except (KeyboardInterrupt, EOFError):
                self._shutdown()
                raise SystemExit(0)

            if not command:
                continue
            if command.lower() in ("back", "menu"):
                break
            if command.lower() in ("sleep", "quit", "exit", "goodbye"):
                self._shutdown()
                raise SystemExit(0)

            self._set_status("processing")
            self._log_msg("user", command)

            response = self._safe_execute(command)
            self._set_status("idle")

            if response:
                print(f"  JARVIS > {response}\n")
                self._log_msg("jarvis", response)
                self.speaker.speak(response)

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _safe_execute(self, command: str) -> str:
        """Run command through the router, catching and logging any error."""
        try:
            return self.router.execute(command)
        except Exception as e:
            logger.error("Router execute error: %s", e)
            self._set_status("error")
            return f"Something went wrong: {e}"

    def _shutdown(self):
        print(f"\n  {self.name} > Goodbye, sir.\n")
        logger.info("JARVIS shutting down.")
        if self.hud:
            self.hud.stop()
