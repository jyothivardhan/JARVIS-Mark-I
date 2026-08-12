"""
query.py
Detects when the user is asking about something stored in memory
and returns the corresponding storage key.

Returns the memory key string, or None if the text is not a memory query.
"""
import re
from core.logger import get_logger

logger = get_logger(__name__)

# (compiled regex, memory key)
_PATTERNS: list[tuple[re.Pattern, str]] = [
    # Name
    (re.compile(r"what(?:'?s| is) my name\??",                    re.IGNORECASE), "name"),
    (re.compile(r"(?:do you know |tell me )?what(?:'?s| is) my name\??",
                                                                  re.IGNORECASE), "name"),
    # Language
    (re.compile(r"what(?:'?s| is) my favou?rite language\??",     re.IGNORECASE), "favorite_language"),
    # Color
    (re.compile(r"what(?:'?s| is) my favou?rite colou?r\??",      re.IGNORECASE), "favorite_color"),
    # Food
    (re.compile(r"what(?:'?s| is) my favou?rite food\??",         re.IGNORECASE), "favorite_food"),
    # Age
    (re.compile(r"what(?:'?s| is) my age\??",                     re.IGNORECASE), "age"),
    (re.compile(r"how old am i\??",                               re.IGNORECASE), "age"),
    # Location
    (re.compile(r"where (?:do i live|am i based)\??",             re.IGNORECASE), "location"),
    (re.compile(r"what(?:'?s| is) my location\??",                re.IGNORECASE), "location"),
    # Origin
    (re.compile(r"where am i from\??",                            re.IGNORECASE), "origin"),
    (re.compile(r"what(?:'?s| is) my origin\??",                  re.IGNORECASE), "origin"),
    # Job
    (re.compile(r"what(?:'?s| is) my job\??",                     re.IGNORECASE), "job"),
    (re.compile(r"what do i do (?:for a living|for work)\??",     re.IGNORECASE), "job"),
    # Hobby
    (re.compile(r"what(?:'?s| is) my hobby\??",                   re.IGNORECASE), "hobby"),
    (re.compile(r"what do i (?:enjoy|like|love)\??",              re.IGNORECASE), "hobby"),
]


class MemoryQuery:

    def find_key(self, text: str) -> str | None:
        """
        Return the memory key the user is asking about, or None.
        """
        text = text.strip()
        for pattern, key in _PATTERNS:
            if pattern.search(text):
                logger.debug("Memory query matched key: %s", key)
                return key
        return None