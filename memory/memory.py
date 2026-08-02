import json
import os


class Memory:

    def __init__(self, file_path=None):
        if file_path is None:
            # Anchor to this file's directory so Memory works no matter
            # where the script is run from.
            base_dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(base_dir, "user_memory.json")

        self.file_path = file_path

        if not os.path.exists(self.file_path):
            self._write({})

    def _write(self, data):
        # Write to a temp file first, then replace — avoids a corrupted
        # file if the process dies mid-write.
        tmp_path = self.file_path + ".tmp"
        with open(tmp_path, "w") as file:
            json.dump(data, file, indent=4)
        os.replace(tmp_path, self.file_path)

    def load(self):
        try:
            with open(self.file_path, "r") as file:
                return json.load(file)
        except (json.JSONDecodeError, FileNotFoundError):
            # Corrupted or missing file — reset instead of crashing.
            self._write({})
            return {}

    def save(self, data):
        self._write(data)

    def remember(self, key, value):
        data = self.load()
        data[key] = value
        self.save(data)

    def recall(self, key):
        data = self.load()
        return data.get(key)
