"""
extractor.py
Extracts key-value facts from natural-language user statements.

Returns (key: str, value: str) or None if no pattern matches.
"""
import re
from core.logger import get_logger

logger = get_logger(__name__)

# (compiled regex, memory key)
_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"my name is (.+)",                  re.IGNORECASE), "name"),
    (re.compile(r"call me (.+)",                     re.IGNORECASE), "name"),
    (re.compile(r"my favou?rite language is (.+)",   re.IGNORECASE), "favorite_language"),
    (re.compile(r"my favou?rite colou?r is (.+)",    re.IGNORECASE), "favorite_color"),
    (re.compile(r"my favou?rite food is (.+)",       re.IGNORECASE), "favorite_food"),
    (re.compile(r"my age is (\d+)",                  re.IGNORECASE), "age"),
    (re.compile(r"i(?:'m| am) (\d+)(?: years? old)?",re.IGNORECASE), "age"),
    (re.compile(r"i live in (.+)",                   re.IGNORECASE), "location"),
    (re.compile(r"my location is (.+)",              re.IGNORECASE), "location"),
    (re.compile(r"i(?:'m| am) from (.+)",            re.IGNORECASE), "origin"),
    (re.compile(r"my job is (.+)",                   re.IGNORECASE), "job"),
    (re.compile(r"i work (?:as|at) (.+)",            re.IGNORECASE), "job"),
    (re.compile(r"my hobby is (.+)",                 re.IGNORECASE), "hobby"),
    (re.compile(r"i (?:enjoy|love|like) (.+)",       re.IGNORECASE), "hobby"),
]

# Characters to strip from the captured value's edges
_STRIP_CHARS = " .,!?"


class MemoryExtractor:

    def extract(self, text: str):
        """
        Scan `text` for a memorisable fact.

        Returns:
            (key, value)  tuple if a pattern matches.
            None          if nothing is found.
        """
        text = text.strip()
        for pattern, key in _PATTERNS:
            match = pattern.search(text)
            if match:
                value = match.group(1).strip(_STRIP_CHARS)
                if value:
                    logger.debug("Extracted memory: %s = %s", key, value)
                    return key, value
        return None