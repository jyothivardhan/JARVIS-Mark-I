import os
import platform
from datetime import datetime


class SystemCommands:

    @staticmethod
    def clear():
        os.system("cls" if os.name == "nt" else "clear")

    @staticmethod
    def current_time():
        return datetime.now().strftime("%I:%M %p")

    @staticmethod
    def current_date():
        return datetime.now().strftime("%d-%m-%Y")

    @staticmethod
    def system_info():
        return f"{platform.system()} {platform.release()}"