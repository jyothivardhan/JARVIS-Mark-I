"""
llm.py
Handles all communication between JARVIS and the local Ollama model.
Supports multi-turn conversation history with a rolling window.
"""
import re
import ollama

from config.settings import MODEL, MAX_HISTORY
from core.logger import get_logger

logger = get_logger(__name__)

_SYSTEM_PROMPT = """You are JARVIS, an intelligent offline AI assistant.

Rules:
- Never reveal that you are Qwen, Llama, or any other underlying model.
- Always introduce yourself as JARVIS.
- Answer only in English.
- Keep responses under 3 sentences unless the user explicitly asks for more detail.
- Be professional, concise, and helpful.
- Do NOT include chain-of-thought or <think> blocks in your response — respond directly.
"""

# Regex to strip Qwen3 / CoT <think>…</think> blocks from responses
_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


class LLM:
    def __init__(self, model: str = None):
        self.model = model or MODEL
        # Each entry: {"role": "user"|"assistant", "content": str}
        self.conversation_history: list[dict] = []
        # Keep last N *messages* (2 per turn: user + assistant)
        self._max_messages = MAX_HISTORY * 2

    # ── Connection ────────────────────────────────────────────────────────────
    def check_connection(self) -> bool:
        """Return True if the Ollama daemon is reachable."""
        try:
            ollama.list()
            return True
        except Exception:
            return False

    # ── Generation ────────────────────────────────────────────────────────────
    def generate(self, prompt: str) -> str:
        """
        Generate a response while maintaining multi-turn conversation history.
        Automatically strips CoT <think> blocks from the reply.
        """
        self.conversation_history.append({"role": "user", "content": prompt})

        # system prompt + rolling history window
        messages = [{"role": "system", "content": _SYSTEM_PROMPT}]
        messages.extend(self.conversation_history[-self._max_messages:])

        try:
            response = ollama.chat(model=self.model, messages=messages)
            reply: str = response["message"]["content"]

            # Strip any CoT thinking block
            reply = _THINK_RE.sub("", reply).strip()

            self.conversation_history.append(
                {"role": "assistant", "content": reply}
            )
            logger.debug("LLM reply (%d chars): %s…", len(reply), reply[:80])
            return reply

        except Exception as e:
            logger.error("LLM generate error: %s", e)
            # Pop the user message so history stays consistent
            self.conversation_history.pop()
            return f"[ERROR] Couldn't reach model '{self.model}': {e}"

    # ── History management ────────────────────────────────────────────────────
    def clear_history(self):
        """Wipe conversation history (start a fresh session)."""
        self.conversation_history.clear()
        logger.info("Conversation history cleared.")

    def get_history_length(self) -> int:
        return len(self.conversation_history) // 2  # number of full turns

    # ── Model management ──────────────────────────────────────────────────────
    def get_model(self) -> str:
        return self.model

    def change_model(self, model: str):
        self.model = model
        self.clear_history()
        logger.info("Model changed to '%s'.", model)

    def list_models(self) -> list:
        try:
            result = ollama.list()
            return [m["model"] for m in result.get("models", [])]
        except Exception:
            return []
