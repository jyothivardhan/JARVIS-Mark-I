"""
tests/test_tools.py
Unit tests for system_tools, web_tools, and vision_tools.
Network calls are mocked; no real HTTP requests are made.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest
from unittest.mock import patch, MagicMock


# ── SystemTools ───────────────────────────────────────────────────────────────
class TestSystemTools(unittest.TestCase):

    def setUp(self):
        from tools.system_tools import SystemTools
        self.t = SystemTools()

    def test_get_time_format(self):
        result = self.t.get_time()
        self.assertTrue(
            "AM" in result or "PM" in result,
            msg=f"Expected AM or PM in time string, got: {result}"
        )
        self.assertTrue(result.startswith("The current time"))

    def test_get_date_format(self):
        result = self.t.get_date()
        self.assertTrue(result.startswith("Today is"))

    def test_get_system_info(self):
        result = self.t.get_system_info()
        self.assertIn("Running", result)

    def test_get_battery_no_psutil_message(self):
        # psutil may or may not be installed — just ensure no crash
        result = self.t.get_battery()
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_get_cpu_no_crash(self):
        result = self.t.get_cpu_usage()
        self.assertIsInstance(result, str)

    def test_get_memory_no_crash(self):
        result = self.t.get_memory_usage()
        self.assertIsInstance(result, str)

    def test_open_browser(self):
        with patch("webbrowser.open") as mock_open:
            result = self.t.open_application("browser")
            mock_open.assert_called_once()
            self.assertIn("browser", result.lower())

    def test_open_notepad(self):
        with patch("subprocess.Popen") as mock_popen:
            result = self.t.open_application("notepad")
            self.assertIn("notepad", result.lower())


# ── WebTools ──────────────────────────────────────────────────────────────────
class TestWebTools(unittest.TestCase):

    def setUp(self):
        from tools.web_tools import WebTools
        self.t = WebTools()

    def _mock_urlopen(self, data: dict):
        """Return a context-manager mock that yields JSON bytes."""
        import json
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(data).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        return mock_resp

    def test_search_returns_abstract(self):
        payload = {"AbstractText": "Python is a programming language.", "RelatedTopics": []}
        with patch("urllib.request.urlopen", return_value=self._mock_urlopen(payload)):
            result = self.t.search_web("Python")
        self.assertIn("Python", result)

    def test_search_falls_back_to_topics(self):
        payload = {
            "AbstractText": "",
            "RelatedTopics": [{"Text": "Python is great."}],
        }
        with patch("urllib.request.urlopen", return_value=self._mock_urlopen(payload)):
            result = self.t.search_web("Python")
        self.assertIn("Python", result)

    def test_search_no_result(self):
        payload = {"AbstractText": "", "RelatedTopics": []}
        with patch("urllib.request.urlopen", return_value=self._mock_urlopen(payload)):
            result = self.t.search_web("xyzzy123")
        self.assertIn("No instant answer", result)

    def test_weather_parsing(self):
        payload = {
            "current_condition": [{
                "temp_C": "28",
                "FeelsLikeC": "30",
                "weatherDesc": [{"value": "Sunny"}],
                "humidity": "60",
                "windspeedKmph": "15",
            }]
        }
        with patch("urllib.request.urlopen", return_value=self._mock_urlopen(payload)):
            result = self.t.get_weather("London")
        self.assertIn("Sunny", result)
        self.assertIn("28", result)

    def test_web_network_error(self):
        import urllib.error
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
            result = self.t.search_web("anything")
        self.assertIn("failed", result.lower())


# ── VisionTools ───────────────────────────────────────────────────────────────
class TestVisionTools(unittest.TestCase):

    def setUp(self):
        from tools.vision_tools import VisionTools
        self.t = VisionTools()

    def test_screenshot_saves_file(self):
        mock_img = MagicMock()
        with patch("tools.vision_tools._PIL", True), \
             patch("tools.vision_tools.ImageGrab") as mock_grab, \
             patch("os.makedirs"):
            mock_grab.grab.return_value = mock_img
            result = self.t.capture_screenshot()
        self.assertIn("saved", result.lower())

    def test_screenshot_without_pil(self):
        with patch("tools.vision_tools._PIL", False):
            result = self.t.capture_screenshot()
        self.assertIn("not installed", result.lower())

    def test_clipboard_reads_text(self):
        with patch("tools.vision_tools._PYPERCLIP", True), \
             patch("tools.vision_tools.pyperclip") as mock_pc:
            mock_pc.paste.return_value = "hello world"
            result = self.t.read_clipboard()
        self.assertIn("hello world", result)

    def test_clipboard_empty(self):
        with patch("tools.vision_tools._PYPERCLIP", True), \
             patch("tools.vision_tools.pyperclip") as mock_pc:
            mock_pc.paste.return_value = ""
            result = self.t.read_clipboard()
        self.assertIn("empty", result.lower())

    def test_clipboard_without_pyperclip(self):
        with patch("tools.vision_tools._PYPERCLIP", False):
            result = self.t.read_clipboard()
        self.assertIn("not installed", result.lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
