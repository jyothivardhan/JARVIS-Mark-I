from commands.system import SystemCommands
from commands.help import HelpCommand


class CommandRouter:

    def __init__(self, llm, memory):
        self.llm = llm
        self.memory= memory

        self.commands = {
            "help": HelpCommand.show,
            "time": SystemCommands.current_time,
            "date": SystemCommands.current_date,
            "system": SystemCommands.system_info,
            "version": self.version,
            "model": self.llm.get_model,
            "clear": self.clear_screen
        }

    def version(self):
        return "Project JARVIS v0.2"

    def clear_screen(self):
        SystemCommands.clear()
        return None
    
    def execute(self, command):
        if command.startswith("remember "):

            parts = command.split(maxsplit=2)

            if len(parts) < 3:
                return "Usage: remember <key> <value>"

            key = parts[1]
            value = parts[2]

            self.memory.remember(key, value)

            return f"I'll remember that. ({key} = {value})"


        if command.startswith("recall "):

            parts = command.split(maxsplit=1)

            if len(parts) < 2:
                return "Usage: recall <key>"

            key = parts[1]

            value = self.memory.recall(key)

            if value is None:
                return "I don't remember anything for that key."

            return value
        command = command.strip().lower()

        if command in self.commands:
            return self.commands[command]()

        return self.llm.generate(command)