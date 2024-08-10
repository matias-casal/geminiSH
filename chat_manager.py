# chat.py

import json
import os

FIRST_RUN_THRESHOLD = 3

class ChatManager:
    HISTORY_FILE_NAME = "history.json"
    
    def __init__(self, config_manager, output_manager, input_manager, state_manager):
        self.config_manager = config_manager
        self.output_manager = output_manager
        self.input_manager = input_manager
        self.state_manager = state_manager
        self.chat_history = self.load_chat_history()

    def load_chat_history(self):
        """Carga el historial de chat desde el archivo history.json."""
        history_file = os.path.join(self.config_manager.directory, self.config_manager.DEFAULT_DIR, self.HISTORY_FILE_NAME)
        if os.path.exists(history_file):
            with open(history_file, "r") as f:
                chat_history = json.load(f)
                if len(chat_history.keys()) <= FIRST_RUN_THRESHOLD:
                    self.state_manager.set_first_run(True)
                return chat_history
        else:
            with open(history_file, "w") as f:
                json.dump({}, f, indent=4)
            self.state_manager.set_first_run(True)
            return {}

    def save_chat_history(self):
        """Guarda el historial de chat en el archivo history.json."""
        history_file = os.path.join(self.config_manager.get_agent_directory(), self.HISTORY_FILE_NAME)
        with open(history_file, "w") as f:
            json.dump(self.chat_history, f, indent=4)

    def add_user_message(self, content):
        """Añade un nuevo mensaje al historial de chat."""
        return