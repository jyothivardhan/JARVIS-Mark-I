"""
tests/test_function_agent.py
Tests for FunctionAgent classification and dispatch logic.
Mocks out LLM, memory, and tools so no network or mic is needed.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest
from unittest.mock import MagicMock, patch

from agents.function_agent import FunctionAgent, ActionType


def _make_agent():
    llm    = MagicMock()
    llm.generate.return_value = "LLM response"
    memory = MagicMock()
    memory.recall.return_value = "vardhan"
    vm     = MagicMock()
    vm.is_available.return_value = False
    agent  = FunctionAgent(llm, memory, vm)
    # Inject mock tools so no real psutil/requests are needed
    sys_mock = MagicMock()
    sys_mock.get_time.return_value = "It is 10:00 AM."
    sys_mock.get_date.return_value = "Today is Tuesday, 12 August 2026."
    sys_mock.get_battery.return_value = "Battery: 80% — charging."
    sys_mock.get_cpu_usage.return_value = "CPU usage: 12.3%"
    sys_mock.get_memory_usage.return_value = "RAM: 6.1 GB used."
    sys_mock.get_system_info.return_value = "Windows 11 (AMD64)."
    sys_mock.open_application.return_value = "Opening notepad."
    web_mock = MagicMock()
    web_mock.get_weather.return_value = "Sunny, 28°C."
    web_mock.search_web.return_value  = "Search result."
    vis_mock = MagicMock()
    vis_mock.capture_screenshot.return_value = "Screenshot saved."
    vis_mock.read_clipboard.return_value     = "Clipboard: hello"
    agent._tools = {"system": sys_mock, "web": web_mock, "vision": vis_mock}
    return agent


class TestClassify(unittest.TestCase):

    def setUp(self):
        self.agent = _make_agent()

    def _cls(self, text):
        action, tool = self.agent.classify(text)
        return action, tool

    # ── Memory store ──────────────────────────────────────────────────────────
    def test_store_name(self):
        a, t = self._cls("my name is Vardhan")
        self.assertEqual(a, ActionType.MEMORY_STORE)

    def test_store_remember(self):
        a, t = self._cls("remember hobby chess")
        self.assertEqual(a, ActionType.MEMORY_STORE)

    def test_store_favourite(self):
        a, t = self._cls("my favourite language is Python")
        self.assertEqual(a, ActionType.MEMORY_STORE)

    # ── Memory recall ─────────────────────────────────────────────────────────
    def test_recall_name(self):
        a, t = self._cls("what is my name?")
        self.assertEqual(a, ActionType.MEMORY_RECALL)

    def test_recall_do_you_remember(self):
        a, t = self._cls("do you remember my name?")
        self.assertEqual(a, ActionType.MEMORY_RECALL)

    # ── Tools ─────────────────────────────────────────────────────────────────
    def test_tool_time(self):
        a, t = self._cls("what is the time")
        self.assertEqual(a, ActionType.TOOL)
        self.assertEqual(t, "time")

    def test_tool_date(self):
        a, t = self._cls("what's the date today")
        self.assertEqual(a, ActionType.TOOL)
        self.assertEqual(t, "date")

    def test_tool_weather(self):
        a, t = self._cls("what's the weather in London")
        self.assertEqual(a, ActionType.TOOL)
        self.assertEqual(t, "weather")

    def test_tool_battery(self):
        a, t = self._cls("check battery")
        self.assertEqual(a, ActionType.TOOL)
        self.assertEqual(t, "battery")

    def test_tool_cpu(self):
        a, t = self._cls("what is the cpu usage")
        self.assertEqual(a, ActionType.TOOL)
        self.assertEqual(t, "cpu")

    def test_tool_search(self):
        a, t = self._cls("search for Python tutorials")
        self.assertEqual(a, ActionType.TOOL)
        self.assertEqual(t, "search")

    def test_tool_screenshot(self):
        a, t = self._cls("take a screenshot")
        self.assertEqual(a, ActionType.TOOL)
        self.assertEqual(t, "screenshot")

    def test_tool_open(self):
        a, t = self._cls("open notepad")
        self.assertEqual(a, ActionType.TOOL)
        self.assertEqual(t, "open")

    # ── General ───────────────────────────────────────────────────────────────
    def test_general(self):
        a, t = self._cls("Explain quantum entanglement")
        self.assertEqual(a, ActionType.GENERAL)
        self.assertIsNone(t)


class TestDispatch(unittest.TestCase):

    def setUp(self):
        self.agent = _make_agent()

    def test_run_time(self):
        result = self.agent.run("what is the time")
        self.assertIn("AM", result)

    def test_run_date(self):
        result = self.agent.run("what is today's date")
        self.assertIn("Tuesday", result)

    def test_run_weather(self):
        result = self.agent.run("weather in London")
        self.assertIn("Sunny", result)

    def test_run_general_calls_llm(self):
        result = self.agent.run("Tell me a joke")
        self.agent.llm.generate.assert_called()
        self.assertEqual(result, "LLM response")

    def test_run_store(self):
        result = self.agent.run("my name is Vardhan")
        self.agent.memory.remember.assert_called_with("name", "Vardhan")

    def test_run_recall(self):
        result = self.agent.run("what is my name?")
        self.assertIn("vardhan", result.lower())

    def test_empty_command_returns_empty(self):
        result = self.agent.run("")
        self.assertEqual(result, "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
