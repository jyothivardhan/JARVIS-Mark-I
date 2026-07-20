from commands.system import SystemCommands
from commands.help import HelpCommand


class CommandRouter:

    def __init__(self, llm):
        self.llm = llm

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

        command = command.strip().lower()

        if command in self.commands:
            return self.commands[command]()

        return self.llm.generate(command)