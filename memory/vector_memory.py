"""
vector_memory.py
Semantic (vector) memory for JARVIS.

Stores text passages as sentence embeddings and retrieves the most
semantically similar ones when queried.

Storage format: JSON list of {text, embedding, timestamp}
Similarity:     cosine similarity via numpy (no faiss/annoy needed)

Optional dependency: sentence-transformers  (pip install sentence-transformers)
If not installed, is_available() returns False and all operations are no-ops.
"""
import os
import json
import time

import numpy as np

from config.settings import VECTOR_MEMORY_FILE, VECTOR_EMBEDDING_MODEL, VECTOR_TOP_K
from core.logger import get_logger

logger = get_logger(__name__)

try:
    from sentence_transformers import SentenceTransformer
    _ST_AVAILABLE = True
except ImportError:
    _ST_AVAILABLE = False
    logger.warning(
        "sentence-transformers not installed — vector memory is disabled. "
        "Install with: pip install sentence-transformers"
    )


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two 1-D vectors."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


class VectorMemory:
    """
    Semantic vector memory backed by a JSON file.

    Public API
    ──────────
      store(text)              embed and persist a text passage
      search(query, top_k=N)   return the N most similar stored passages
      is_available()           True if sentence-transformers is installed
    """

    def __init__(
        self,
        file_path:   str = VECTOR_MEMORY_FILE,
        model_name:  str = VECTOR_EMBEDDING_MODEL,
        top_k:       int = VECTOR_TOP_K,
    ):
        self._file  = file_path
        self._top_k = top_k
        self._model = None
        self._entries: list[dict] = []   # {text, embedding, timestamp}

        if _ST_AVAILABLE:
            try:
                logger.info("Loading embedding model '%s'…", model_name)
                self._model = SentenceTransformer(model_name)
                logger.info("Embedding model ready.")
            except Exception as e:
                logger.error("Could not load embedding model: %s", e)

        self._load()

    # ── Availability ──────────────────────────────────────────────────────────
    def is_available(self) -> bool:
        return self._model is not None

    # ── Persistence ───────────────────────────────────────────────────────────
    def _load(self):
        if not os.path.exists(self._file):
            return
        try:
            with open(self._file, "r", encoding="utf-8") as f:
                self._entries = json.load(f)
            logger.debug("Vector memory: loaded %d entries.", len(self._entries))
        except Exception as e:
            logger.warning("Could not load vector memory file: %s", e)
            self._entries = []

    def _save(self):
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self._file)), exist_ok=True)
            tmp = self._file + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self._entries, f, indent=2)
            os.replace(tmp, self._file)
        except Exception as e:
            logger.error("Could not save vector memory: %s", e)

    # ── Public API ────────────────────────────────────────────────────────────
    def store(self, text: str):
        """Embed `text` and add it to the persistent store."""
        if not self._model:
            return
        try:
            embedding = self._model.encode(text).tolist()
            self._entries.append({
                "text":      text,
                "embedding": embedding,
                "timestamp": time.time(),
            })
            self._save()
        except Exception as e:
            logger.error("Vector store error: %s", e)

    def search(self, query: str, top_k: int = None) -> list[dict]:
        """
        Return the top-k most semantically similar stored entries.
        Each result dict has keys: text (str), score (float).
        """
        if not self._model or not self._entries:
            return []

        k = top_k or self._top_k
        try:
            q_vec = self._model.encode(query)
            scored = [
                {
                    "text":  entry["text"],
                    "score": _cosine(q_vec, np.array(entry["embedding"])),
                }
                for entry in self._entries
            ]
            scored.sort(key=lambda x: x["score"], reverse=True)
            return scored[:k]
        except Exception as e:
            logger.error("Vector search error: %s", e)
            return []

    def count(self) -> int:
        return len(self._entries)
