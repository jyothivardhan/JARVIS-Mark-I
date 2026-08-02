import re


class MemoryQuery:

    def find_key(self, text):
        """
        Detects whether the user is asking
        about something stored in memory.

        Returns:
            key or None
        """

        text = text.strip().lower()

        patterns = [
            (r"what('?s| is) my name\??", "name"),
            (r"what('?s| is) my favorite language\??", "favorite_language"),
            (r"what('?s| is) my favourite language\??", "favorite_language"),
            (r"what('?s| is) my favorite color\??", "favorite_color"),
            (r"what('?s| is) my favourite color\??", "favorite_color"),
        ]

        for pattern, key in patterns:

            if re.fullmatch(pattern, text):
                return key

        return None