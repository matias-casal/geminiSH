import os
import google.generativeai as genai
from google.ai.generativelanguage import Tool, Content, Part
from rich.console import Console

class ModelManager:
    MODEL_PRESENTATION = "GEMINI SH"
    
    def __init__(self, config_manager, state_manager, function_manager, output_manager, chat_manager):
        self.config_manager = config_manager
        self.state_manager = state_manager
        self.function_manager = function_manager
        self.output_manager = output_manager
        self.chat_manager = chat_manager
        self.model = self.init_model()
        self.console = Console()

    def first_message(self):
        """Método para enviar el primer mensaje al modelo."""
        self.output_manager.print(f"\n\n# {self.MODEL_PRESENTATION}", style="bold magenta", markdown=True)
        if self.state_manager.is_first_run():    
            first_runs_path = os.path.join(self.config_manager.directory, "prompts", "first_runs.md")
            if os.path.exists(first_runs_path):
                with open(first_runs_path, "r") as f:
                    first_runs_text = f.read()
                    self.chat_manager.add_text_part('model', first_runs_text)
                    self.output_manager.print(first_runs_text, style="bold magenta", markdown=True)
            
    def init_model(self):
        """Inicializa el modelo y trae las funciones declaradas."""
        model_name = self.config_manager.config["MODEL_NAME"]
        max_output_tokens = self.config_manager.config["MODEL_MAX_OUTPUT_TOKENS"]
        safety_settings = self.config_manager.config["MODEL_SAFETY_SETTINGS"]
        system_instructions = self.state_manager.state["system_instructions"]
        functions_tools = Tool(function_declarations=self.function_manager.get_as_declarations())
        self.output_manager.debug(f"Model name: {model_name}")
        api_key = self.config_manager.get_api_key()
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name,
            generation_config=genai.GenerationConfig(max_output_tokens=None),
            tools=functions_tools,
            safety_settings=safety_settings,
            system_instruction=system_instructions
        )
        return model
            
    def generate_content(self):
        """Método para enviar un mensaje al modelo."""
        # try:
        for part in self.chat_manager.current_chat:
            self.output_manager.debug(f"Chat part: {part}", 2)
        with self.console.status("[bold blue]Gemini is thinking...[/bold blue]"):
            response = self.model.generate_content(self.chat_manager.current_chat)
        return self.handle_gemini_response(response)
        # except Exception as e:
        #     self.output_manager.debug(f"Error generating content: {e}", 3)
        #     # TODO: Ask to retry
        #     return None
    
    def message_to_proto(self, message):
        """Convierte un mensaje en un objeto proto Content."""
        if isinstance(message, str):
            return Content(
                role="user",
                parts=[Part(text=message)]
            )
            
    def handle_gemini_response(self, response):
        """Handles the response from Google Gemini, extracting text and executing functions."""
        response_dict = type(response).to_dict(response)
        
        if not (response_dict.get('candidates') and 
                response_dict['candidates'][0].get('content') and 
                response_dict['candidates'][0]['content'].get('parts')):
            self.output_manager.warning("The model did not provide a response.")
            self.output_manager.debug(f"Model response: {response_dict}")
            return None
        
        function_responses = []
        gemini_shown = False
        for part in response_dict['candidates'][0]['content']['parts']:
            if 'text' in part:
                if not gemini_shown:
                    self.output_manager.print("[bold blue]Gemini:[/bold blue]")
                    self.output_manager.print(part['text'], style="bold blue", markdown=True)
                    gemini_shown = True
                self.chat_manager.add_text_part('model', part['text'])
            if 'function_call' in part and part['function_call']:
                with self.console.status("[bold yellow]Gemini is executing function...[/bold yellow]"):
                    function_call = part['function_call']
                    function_name = function_call.get('name')
                    function_args = function_call.get('args', {})
                    self.chat_manager.add_function_call('model', function_name, function_args)
                    response = self.function_manager.execute_function(function_name, function_args)
                    function_responses.append((function_name, response))
                
        for function_name, response in function_responses:
            if isinstance(response, str):
                self.chat_manager.add_function_response('user', function_name, response)
            elif isinstance(response, dict):
                if 'response' in response:
                    self.chat_manager.add_function_response('user', function_name, response['response'])
                if 'response_to_agent' in response:
                    self.function_manager.handle_agent_functions_response(response['response_to_agent'])
            