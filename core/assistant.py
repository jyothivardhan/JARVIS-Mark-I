from core.llm import LLM
from commands.router import CommandRouter
from memory.memory import Memory

class Assistant:

    def __init__(self):
        self.name = "JARVIS"
        self.llm = LLM()
        self.memory = Memory()
        self.router = CommandRouter(self.llm, self.memory)

    def start(self):

        print("=" * 40)
        print(f"        {self.name}")
        print("=" * 40)

        if not self.llm.check_connection():
            print("\n[ERROR] Ollama is not running.")
            print("Start Ollama and try again.")
            return

        print(f"\nConnected to: {self.llm.get_model()}")
        print("Type 'sleep' to quit.\n")

        while True:

            command = input("You > ").strip()

            if command.lower() == "sleep":
                print("\nYes sir\n")
                break

            try:
                response = self.router.execute(command)
            except Exception as e:
                response = f"[ERROR] Something went wrong: {e}"

            if response:
                print(f"\nJARVIS > {response}\n")
