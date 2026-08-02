"""
llm.py

Handles all communication between Project JARVIS and the local Ollama model.
"""

import ollama
from config.settings import MODEL


class LLM:
    def __init__(self, model=None):
        """
        Initialize the LLM.

        Args:
            model (str): Name of the Ollama model. Defaults to config/settings.MODEL.
        """
        self.model = model or MODEL

        self.system_prompt = """
        You are JARVIS, an intelligent offline AI assistant.

        Rules:
        - Never say you are Qwen.
        - Introduce yourself only as JARVIS.
        - Answer only in English.
        - Keep responses under 3 sentences unless asked for detail.
        - Be professional, concise, and helpful.
        """

    def check_connection(self):
        """
        Check whether Ollama is running.
        """
        try:
            ollama.list()
            return True
        except Exception:
            return False

    def generate(self, prompt):

        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self.system_prompt
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            return response["message"]["content"]

        except Exception as e:
            return f"[ERROR] Couldn't reach the model ({self.model}): {e}"

    def get_model(self):
        """
        Return the current model.
        """
        return self.model

    def change_model(self, model):
        """
        Change the active model.
        """
        self.model = model

    def list_models(self):
        """
        Return all locally installed Ollama models.
        """
        try:
            models = ollama.list()

            return [model["model"] for model in models["models"]]

        except Exception:
            return []
