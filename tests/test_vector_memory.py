"""
tests/test_vector_memory.py
Tests for VectorMemory — sentence-transformers is mocked so the test
runs even without the library installed.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import unittest
import tempfile
import numpy as np
from unittest.mock import MagicMock, patch


class TestVectorMemoryMocked(unittest.TestCase):
    """
    Uses a mock SentenceTransformer so the test never needs the real library.
    Embeddings are simple 3-D vectors to keep assertions easy.
    """

    def _make_vm(self, tmp_file: str):
        mock_model = MagicMock()
        # Deterministic embeddings: "apple" → [1,0,0], "orange" → [0.9,0.1,0]
        def fake_encode(text):
            if "apple" in text.lower():
                return np.array([1.0, 0.0, 0.0])
            if "orange" in text.lower():
                return np.array([0.9, 0.1, 0.0])
            return np.array([0.0, 0.0, 1.0])

        mock_model.encode.side_effect = fake_encode

        with patch("memory.vector_memory._ST_AVAILABLE", True), \
             patch("memory.vector_memory.SentenceTransformer", return_value=mock_model, create=True):
            from memory.vector_memory import VectorMemory
            vm = VectorMemory(file_path=tmp_file)
        return vm

    def test_store_and_count(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp = f.name
        try:
            vm = self._make_vm(tmp)
            self.assertEqual(vm.count(), 0)
            vm.store("apple fruit")
            self.assertEqual(vm.count(), 1)
        finally:
            os.unlink(tmp)

    def test_search_returns_closest(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp = f.name
        try:
            vm = self._make_vm(tmp)
            vm.store("apple fruit")
            vm.store("completely unrelated xyz")
            results = vm.search("apple")
            self.assertTrue(len(results) > 0)
            self.assertIn("apple", results[0]["text"])
            # Score should be near 1.0 for apple vs apple query
            self.assertGreater(results[0]["score"], 0.9)
        finally:
            os.unlink(tmp)

    def test_persistence(self):
        """Data written to file should reload on next instantiation."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp = f.name
        try:
            vm = self._make_vm(tmp)
            vm.store("apple fruit")
            # Re-create from same file
            vm2 = self._make_vm(tmp)
            self.assertEqual(vm2.count(), 1)
        finally:
            os.unlink(tmp)

    def test_is_available_true(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp = f.name
        try:
            vm = self._make_vm(tmp)
            self.assertTrue(vm.is_available())
        finally:
            os.unlink(tmp)


class TestVectorMemoryUnavailable(unittest.TestCase):
    """When sentence-transformers is missing everything should be a no-op."""

    def test_not_available(self):
        with patch("memory.vector_memory._ST_AVAILABLE", False):
            with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
                tmp = f.name
            try:
                from memory.vector_memory import VectorMemory
                vm = VectorMemory(file_path=tmp)
                self.assertFalse(vm.is_available())
                vm.store("some text")   # should not raise
                results = vm.search("query")
                self.assertEqual(results, [])
            finally:
                os.unlink(tmp)


if __name__ == "__main__":
    unittest.main(verbosity=2)
