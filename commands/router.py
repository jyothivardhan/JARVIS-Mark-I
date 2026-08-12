"""
router.py
CommandRouter — thin dispatcher that handles built-in commands
and delegates everything else to FunctionAgent.

Built-ins (handled here):
  help     show command reference
  clear    clear the terminal
  version  JARVIS version string
  model    current Ollama model name
  history  dump the last N conversation turns
  models   list locally available Ollama models

Everything else → FunctionAgent (memory / tool / LLM).
"""
import os

from commands.help   import HelpCommand
from commands.system import SystemCommands
from core.logger     import get_logger

logger = get_logger(__name__)


class CommandRouter:

    def __init__(self, llm, memory, vector_memory=None):
        self.llm           = llm
        self.memory        = memory
        self.vector_memory = vector_memory

        # Lazy import so FunctionAgent's own tool imports don't block startup
        from agents.function_agent import FunctionAgent
        self._agent = FunctionAgent(llm, memory, vector_memory)

        # Pure built-ins that don't need the agent
        self._builtins = {
            "help":    HelpCommand.show,
            "clear":   self._clear,
            "version": self._version,
            "model":   self.llm.get_model,
            "models":  self._list_models,
            "history": self._show_history,
        }

    # ── Built-in helpers ──────────────────────────────────────────────────────
    def _version(self) -> str:
        from config.settings import ASSISTANT_NAME, VERSION
        return f"{ASSISTANT_NAME} v{VERSION}"

    def _clear(self):
        SystemCommands.clear()
        return None

    def _list_models(self) -> str:
        models = self.llm.list_models()
        if not models:
            return "No local models found (is Ollama running?)."
        return "Installed models:\n" + "\n".join(f"  • {m}" for m in models)

    def _show_history(self) -> str:
        h = self.llm.conversation_history
        if not h:
            return "No conversation history yet."
        lines = []
        for msg in h[-10:]:          # show last 5 turns (10 messages)
            prefix = "You" if msg["role"] == "user" else "JARVIS"
            lines.append(f"{prefix}: {msg['content'][:120]}")
        return "\n".join(lines)

    # ── Main dispatch ─────────────────────────────────────────────────────────
    def execute(self, command: str):
        """
        Route `command` to the correct handler.

        Returns:
            str | None — response string, or None (e.g. after 'clear').
        """
        if not command or not command.strip():
            return None

        lowered = command.strip().lower()

        if lowered in self._builtins:
            logger.debug("Built-in command: '%s'", lowered)
            return self._builtins[lowered]()

        return self._agent.run(command)
