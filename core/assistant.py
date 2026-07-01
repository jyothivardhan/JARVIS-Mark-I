class Assistant:

    def __init__(self):
        self.name = "JARVIS"

    def start(self):
        print("=" * 36)
        print(f"      {self.name}")
        print("=" * 36)
        print("Type 'exit' to quit.\n")

        while True:
            command = input("You > ").strip().lower()

            if command == "exit":
                print("Goodbye!")
                break

            self.process_command(command)

    def process_command(self, command):
        if command == "wake up jarvis":
            print("JARVIS > Hello Sir, How can I help you today?")

        elif command == "what is your name":
            print(f"JARVIS > My name is {self.name}.")

        else:
            print("JARVIS > Sorry, I don't understand that command yet.")