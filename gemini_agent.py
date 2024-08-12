import sys

from chat_manager import ChatManager
from function_manager import FunctionManager
from output_manager import OutputManager
from input_manager import InputManager
from config_manager import ConfigManager
from state_manager import StateManager
from model_manager import ModelManager

class GeminiAgent:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.output_manager = OutputManager(self.config_manager)
        self.input_manager = InputManager(self.output_manager)
        self.state_manager = StateManager(self.config_manager, self.output_manager)
        self.chat_manager = ChatManager(self.config_manager, self.output_manager, self.input_manager, self.state_manager)
        self.function_manager = FunctionManager(self.config_manager, self.chat_manager, self.output_manager, self.input_manager)
        self.model_manager = ModelManager(self.config_manager, self.state_manager, self.function_manager, self.output_manager, self.input_manager, self.chat_manager)
        self.function_manager.set_model_manager(self.model_manager)
    def run(self):
        """Run the main user interaction loop."""
        self.model_manager.first_message()
        
        # Process arguments if they exist
        args = sys.argv[1:]
        if args:
            initial_input = ' '.join(args)
            self.process_message(initial_input)
        
        while True:
            user_input = self.input_manager.input()
            self.process_message(user_input)

    def process_message(self, user_input):
        """Process the message entered by the user."""
        if len(user_input.split()) == 1 and user_input.lower() in self.function_manager.functions.keys():
            parts = user_input.split()
            function_name = parts[0].lower()
            args = ' '.join(parts[1:]) if len(parts) > 1 else None
            if args is None:
                function_response = self.function_manager.functions[function_name]()
            else:
                function_response = self.function_manager.functions[function_name](args)
            self.chat_manager.add_text_part('user', function_name)
            self.chat_manager.add_function_call('model', function_name, args)
            self.model_manager.handle_function_response(function_name, function_response)
        else:
            self.chat_manager.add_text_part('user', user_input)
        self.model_manager.generate_content()
        

    def exit(self):
        """Exit the main loop."""
        exit()