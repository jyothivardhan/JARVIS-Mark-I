"""
tests/test_multiturn.py
Tests for multi-turn LLM conversation history management.
Ollama is mocked — no running server required.
"""
import sys
import os
import types
import unittest
from unittest.mock import patch, MagicMock

# ── Inject a fake 'ollama' module before anything imports it ──────────────────
_fake_ollama = types.ModuleType("ollama")
_fake_ollama.chat = MagicMock()
_fake_ollama.list = MagicMock(return_value={"models": []})
sys.modules.setdefault("ollama", _fake_ollama)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.llm import LLM  # noqa: E402  (import after sys.modules patch)


def _make_llm(model: str = "test-model") -> LLM:
    return LLM(model=model)


class TestLLMHistory(unittest.TestCase):

    def test_history_grows(self):
        llm = _make_llm()
        mock_resp = {"message": {"content": "Hello!"}}

        with patch("core.llm.ollama.chat", return_value=mock_resp, create=True):
            llm.generate("Hi")

        self.assertEqual(len(llm.conversation_history), 2)    # user + assistant
        self.assertEqual(llm.conversation_history[0]["role"], "user")
        self.assertEqual(llm.conversation_history[1]["role"], "assistant")

    def test_history_cleared(self):
        llm = _make_llm()
        mock_resp = {"message": {"content": "Response"}}

        with patch("core.llm.ollama.chat", return_value=mock_resp, create=True):
            llm.generate("Turn 1")
            llm.generate("Turn 2")

        self.assertEqual(llm.get_history_length(), 2)
        llm.clear_history()
        self.assertEqual(llm.get_history_length(), 0)
        self.assertEqual(llm.conversation_history, [])

    def test_history_sent_to_ollama(self):
        llm = _make_llm()
        mock_resp = {"message": {"content": "Reply"}}

        with patch("core.llm.ollama.chat", return_value=mock_resp, create=True) as mock_chat:
            llm.generate("First message")
            llm.generate("Second message")

        # Second call should include previous turn in messages
        last_call_messages = mock_chat.call_args[1]["messages"]
        roles = [m["role"] for m in last_call_messages]
        self.assertIn("system",    roles)
        self.assertIn("user",      roles)
        self.assertIn("assistant", roles)

    def test_cot_tags_stripped(self):
        llm = _make_llm()
        mock_resp = {
            "message": {"content": "<think>internal thought</think> The answer is 42."}
        }
        with patch("core.llm.ollama.chat", return_value=mock_resp, create=True):
            result = llm.generate("What is 6x7?")

        self.assertNotIn("<think>", result)
        self.assertIn("42", result)

    def test_error_does_not_corrupt_history(self):
        llm = _make_llm()
        with patch("core.llm.ollama.chat", side_effect=Exception("timeout"), create=True):
            result = llm.generate("Will this crash?")

        # History must stay clean (user message rolled back)
        self.assertEqual(len(llm.conversation_history), 0)
        self.assertIn("ERROR", result)

    def test_rolling_window(self):
        """History should not exceed max_messages sent to ollama per call."""
        llm = _make_llm()
        llm._max_messages = 4   # cap at 2 turns sent to API per call
        mock_resp = {"message": {"content": "ok"}}

        call_messages = []
        def capture_chat(**kwargs):
            call_messages.append(len(kwargs["messages"]))
            return mock_resp

        with patch("core.llm.ollama.chat", side_effect=capture_chat, create=True):
            for i in range(5):
                llm.generate(f"Message {i}")

        # After 2nd call, messages sent to API should be capped at system + 4 = 5
        # (the rolling slice is applied each call)
        self.assertLessEqual(max(call_messages), 1 + llm._max_messages + 1)

    def test_model_change_clears_history(self):
        llm = _make_llm()
        mock_resp = {"message": {"content": "ok"}}
        with patch("core.llm.ollama.chat", return_value=mock_resp, create=True):
            llm.generate("hello")
        self.assertGreater(len(llm.conversation_history), 0)

        llm.change_model("new-model")
        self.assertEqual(len(llm.conversation_history), 0)
        self.assertEqual(llm.get_model(), "new-model")


class TestLLMConnection(unittest.TestCase):

    def test_check_connection_true(self):
        llm = _make_llm()
        with patch("core.llm.ollama.list", return_value={}, create=True):
            self.assertTrue(llm.check_connection())

    def test_check_connection_false(self):
        llm = _make_llm()
        with patch("core.llm.ollama.list", side_effect=Exception("refused"), create=True):
            self.assertFalse(llm.check_connection())

    def test_list_models(self):
        llm = _make_llm()
        with patch("core.llm.ollama.list",
                   return_value={"models": [{"model": "qwen3:4b"}, {"model": "llama3"}]},
                   create=True):
            models = llm.list_models()
        self.assertEqual(models, ["qwen3:4b", "llama3"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
