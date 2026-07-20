class HelpCommand:

    @staticmethod
    def show():

        return """
=========================
Available Commands
=========================

help      - Show this menu
clear     - Clear terminal
time      - Show current time
date      - Show today's date
model     - Show current AI model
version   - Show JARVIS version
system    - Show operating system
exit      - Close JARVIS

Anything else is sent to the AI.
"""