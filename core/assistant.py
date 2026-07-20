from core.llm import LLM
from commands.router import CommandRouter

class Assistant:

    def __init__(self):
        self.name = "JARVIS"
        self.llm = LLM()
        self.router = CommandRouter(self.llm)
    def start(self):

        print("=" * 40)
        print(f"        {self.name}")
        print("=" * 40)

        if not self.llm.check_connection():
            print("\n[ERROR] Ollama is not running.")
            print("Start Ollama and try again.")
            return

        print(f"\nConnected to: {self.llm.get_model()}")
        print("Type 'exit' to quit.\n")

        while True:

            command = input("You > ").strip()

            if command.lower() == "exit":
                print("\nGoodbye!\n")
                break

            response = self.router.execute(command)

            if response:
                print(f"\nJARVIS > {response}\n")