"""
function_agent.py
Routes user commands to the correct handler using fast regex classification.

Action types
────────────
  MEMORY_STORE   "my name is …", "remember key value"
  MEMORY_RECALL  "what is my name?", "recall key"
  TOOL           time, date, weather, battery, cpu, ram, search, screenshot, …
  GENERAL        everything else → multi-turn LLM
"""
import re
from enum import Enum, auto
from core.logger import get_logger

logger = get_logger(__name__)


# ── Action type enum ──────────────────────────────────────────────────────────
class ActionType(Enum):
    MEMORY_STORE  = auto()
    MEMORY_RECALL = auto()
    TOOL          = auto()
    GENERAL       = auto()


# ── Classification patterns ───────────────────────────────────────────────────
_MEMORY_STORE_PAT = [
    r"\bmy name is\b",
    r"\bcall me\b",
    r"\bmy favou?rite \w+ is\b",
    r"^remember\s+\S+\s+\S",
    r"\bmy age is\b",
    r"\bi(?:'m| am) \d+ years? old\b",
    r"\bi live in\b",
    r"\bmy location is\b",
    r"\bi(?:'m| am) from\b",
    r"\bmy job is\b",
    r"\bi work (?:as|at)\b",
    r"\bmy hobby is\b",
    r"\bi (?:enjoy|love|like)\b",
    r"\bmy favou?rite food is\b",
]

_MEMORY_RECALL_PAT = [
    r"\bwhat(?:'?s| is) my\b",
    r"^recall\s+\S",
    r"\bdo you remember\b",
    r"\bwhat did i tell you\b",
    r"\bhow old am i\b",
    r"\bwhere do i live\b",
    r"\bwhere am i from\b",
]

# Maps a tool key → its detection regex
_TOOL_PAT: dict[str, str] = {
    "time":         r"\b(what(?:'?s| is) the time|current time|what time is it)\b",
    "date":         r"\b(what(?:'?s| is) (?:the |today'?s? )?date|what(?:'?s)? (?:the |today'?s? )?date|what day is it)\b",
    "weather":      r"\b(weather|temperature|forecast)\b",
    "battery":      r"\b(battery|charge level|charging status)\b",
    "cpu":          r"\b(cpu|processor usage|cpu usage|processor load)\b",
    "memory_usage": r"\b(ram|memory usage|how much (ram|memory))\b",
    "system":       r"\b(system info|os version|operating system|what os)\b",
    "search":       r"\b(search(?: for| the web for)?|look up|find out|google)\b",
    "screenshot":   r"\b(screenshot|capture (the )?screen|take a screenshot)\b",
    "clipboard":    r"\b(clipboard|what'?s? (?:in|on) (?:my )?clipboard)\b",
    "open":         r"\b(open|launch|start)\s+\w+",
}


def _matches(text: str, patterns: list) -> bool:
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


def _detect_tool(text: str) -> str | None:
    for name, pattern in _TOOL_PAT.items():
        if re.search(pattern, text, re.IGNORECASE):
            return name
    return None


# ── FunctionAgent ─────────────────────────────────────────────────────────────
class FunctionAgent:
    """
    Classifies a command and dispatches it to memory, a tool, or the LLM.
    """

    def __init__(self, llm, memory, vector_memory=None):
        self.llm           = llm
        self.memory        = memory
        self.vector_memory = vector_memory
        self._tools        = self._load_tools()

    # ── Tool loader ───────────────────────────────────────────────────────────
    def _load_tools(self) -> dict:
        tools = {}
        try:
            from tools.system_tools import SystemTools
            tools["system"] = SystemTools()
        except Exception as e:
            logger.warning("SystemTools load failed: %s", e)
        try:
            from tools.web_tools import WebTools
            tools["web"] = WebTools()
        except Exception as e:
            logger.warning("WebTools load failed: %s", e)
        try:
            from tools.vision_tools import VisionTools
            tools["vision"] = VisionTools()
        except Exception as e:
            logger.warning("VisionTools load failed: %s", e)
        return tools

    # ── Classification ────────────────────────────────────────────────────────
    def classify(self, text: str) -> tuple[ActionType, str | None]:
        """Return (ActionType, optional_tool_name)."""
        if _matches(text, _MEMORY_STORE_PAT):
            return ActionType.MEMORY_STORE, None
        if _matches(text, _MEMORY_RECALL_PAT):
            return ActionType.MEMORY_RECALL, None
        tool = _detect_tool(text)
        if tool:
            return ActionType.TOOL, tool
        return ActionType.GENERAL, None

    # ── Main dispatch ─────────────────────────────────────────────────────────
    def run(self, command: str) -> str:
        """Classify and execute `command`. Returns a response string."""
        command = command.strip()
        if not command:
            return ""

        action, tool_name = self.classify(command)
        logger.info("Dispatch → %s (tool=%s)", action.name, tool_name)

        if action == ActionType.MEMORY_STORE:
            return self._store(command)
        if action == ActionType.MEMORY_RECALL:
            return self._recall(command)
        if action == ActionType.TOOL and tool_name:
            return self._run_tool(command, tool_name)

        # General: LLM + optionally store to vector memory
        response = self.llm.generate(command)
        self._vector_store(f"Q: {command}\nA: {response}")
        return response

    # ── Memory store ──────────────────────────────────────────────────────────
    def _store(self, command: str) -> str:
        from memory.extractor import MemoryExtractor
        result = MemoryExtractor().extract(command)
        if result:
            key, value = result
            self.memory.remember(key, value)
            return f"Got it — I've noted your {key.replace('_', ' ')} as '{value}'."

        # Manual "remember <key> <value>"
        parts = command.strip().split(maxsplit=2)
        if parts[0].lower() == "remember" and len(parts) >= 3:
            self.memory.remember(parts[1], parts[2])
            return f"Remembered: {parts[1]} = {parts[2]}"

        return self.llm.generate(command)

    # ── Memory recall ─────────────────────────────────────────────────────────
    def _recall(self, command: str) -> str:
        from memory.query import MemoryQuery
        key = MemoryQuery().find_key(command)

        if key:
            value = self.memory.recall(key)
            if value:
                return f"Your {key.replace('_', ' ')} is '{value}'."
            return f"I don't have your {key.replace('_', ' ')} stored yet."

        # Manual "recall <key>"
        parts = command.strip().split(maxsplit=1)
        if parts[0].lower() == "recall" and len(parts) == 2:
            key_raw = parts[1].strip()
            value   = self.memory.recall(key_raw)
            return value if value else f"Nothing stored for '{key_raw}'."

        # Semantic search in vector memory
        if self.vector_memory and self.vector_memory.is_available():
            results = self.vector_memory.search(command)
            if results:
                return results[0]["text"]

        return self.llm.generate(command)

    # ── Tool execution ────────────────────────────────────────────────────────
    def _run_tool(self, command: str, tool: str) -> str:
        sys_t = self._tools.get("system")
        web_t = self._tools.get("web")
        vis_t = self._tools.get("vision")

        try:
            if tool == "time"         and sys_t: return sys_t.get_time()
            if tool == "date"         and sys_t: return sys_t.get_date()
            if tool == "battery"      and sys_t: return sys_t.get_battery()
            if tool == "cpu"          and sys_t: return sys_t.get_cpu_usage()
            if tool == "memory_usage" and sys_t: return sys_t.get_memory_usage()
            if tool == "system"       and sys_t: return sys_t.get_system_info()
            if tool == "screenshot"   and vis_t: return vis_t.capture_screenshot()
            if tool == "clipboard"    and vis_t: return vis_t.read_clipboard()

            if tool == "weather" and web_t:
                m    = re.search(r"weather (?:in |at |for )?([A-Za-z\s]+)",
                                 command, re.IGNORECASE)
                city = m.group(1).strip() if m else "London"
                return web_t.get_weather(city)

            if tool == "search" and web_t:
                m     = re.search(
                    r"(?:search(?: for| the web for)?|look up|find out|google)\s+(.+)",
                    command, re.IGNORECASE
                )
                query = m.group(1).strip() if m else command
                return web_t.search_web(query)

            if tool == "open" and sys_t:
                m   = re.search(r"(?:open|launch|start)\s+(.+)",
                                command, re.IGNORECASE)
                app = m.group(1).strip() if m else ""
                return sys_t.open_application(app)

        except Exception as e:
            logger.error("Tool '%s' raised an error: %s", tool, e)
            return f"The {tool} tool encountered an error: {e}"

        # Matched as a tool but no handler found — fall through to LLM
        return self.llm.generate(command)

    # ── Vector memory helper ──────────────────────────────────────────────────
    def _vector_store(self, text: str):
        if self.vector_memory and self.vector_memory.is_available():
            try:
                self.vector_memory.store(text)
            except Exception as e:
                logger.debug("Vector store skipped: %s", e)
