from chat_manager import ChatManager
from function_manager import FunctionManager
from output_manager import OutputManager
from files_manager import FilesManager
from input_manager import InputManager
from config_manager import ConfigManager
from state_manager import StateManager
from model_manager import ModelManager

class GeminiAgent:
    def __init__(self):
        self.output_manager = OutputManager()
        self.input_manager = InputManager(self.output_manager)
        self.config_manager = ConfigManager(self.input_manager, self.output_manager)
        self.function_manager = FunctionManager(self.config_manager, self.output_manager, self.input_manager)
        self.files_manager = FilesManager(self.config_manager, self.output_manager)
        self.state_manager = StateManager(self.config_manager, self.output_manager)
        self.chat_manager = ChatManager(self.config_manager, self.output_manager, self.input_manager, self.state_manager)
        self.model_manager = ModelManager(self.config_manager, self.state_manager, self.function_manager, self.output_manager, self.chat_manager)

    def run(self):
        """Ejecuta el bucle principal de interacción con el usuario."""
        self.model_manager.first_message()
        while True:
            user_input = self.input_manager.input()
            self.process_message(user_input)

    def process_message(self, message):
        """Procesa el mensaje introducido por el usuario."""
        if len(message.split()) == 1 and message.lower() in self.function_manager.functions:
            self.function_manager.execute_function(message)
        else:
            self.model_manager.generate_content(message)

    def exit(self):
        """Salir del bucle principal."""
        self.output_manager.print("Saliendo...")
        exit()