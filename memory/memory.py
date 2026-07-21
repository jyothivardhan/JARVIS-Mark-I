import json
import os


class Memory:

    def __init__(self, file_path="memory/user_memory.json"):
        self.file_path = file_path

        if not os.path.exists(self.file_path):
            with open(self.file_path, "w") as file:
                json.dump({}, file)

    def load(self):
        with open(self.file_path, "r") as file:
            return json.load(file)

    def save(self, data):
        with open(self.file_path, "w") as file:
            json.dump(data, file, indent=4)

    def remember(self, key, value):
        data = self.load()
        data[key] = value
        self.save(data)

    def recall(self, key):
        data = self.load()
        return data.get(key)