import re


class MemoryExtractor:

    def extract(self, text):
        """
        Extracts important information from user input.

        Returns:
            (key, value) if something should be remembered.
            None otherwise.
        """

        text = text.strip()

        patterns = [
            (r"my name is (.+)", "name"),
            (r"i am (.+)", "name"),
            (r"my favorite language is (.+)", "favorite_language"),
            (r"my favourite language is (.+)", "favorite_language"),
            (r"my favorite color is (.+)", "favorite_color"),
            (r"my favourite color is (.+)", "favorite_color"),
        ]

        for pattern, key in patterns:

            match = re.search(pattern, text, re.IGNORECASE)

            if match:
                value = match.group(1).strip()
                return key, value

        return None