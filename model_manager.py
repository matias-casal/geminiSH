import google.generativeai as genai
from google.ai.generativelanguage import Tool, Content, Part

class ModelManager:
    def __init__(self, config_manager, state_manager, function_manager, output_manager, chat_manager):
        self.config_manager = config_manager
        self.state_manager = state_manager
        self.function_manager = function_manager
        self.output_manager = output_manager
        self.chat_manager = chat_manager
        self.model = self.init_model()

    def first_message(self):
        """Método para enviar el primer mensaje al modelo."""
        if self.state_manager.is_first_run:
            self.output_manager.print(f"\n\n# GEMINI SH", style="bold magenta", markdown=True)
            self.output_manager.print(f"## Bienvenido a Gemini SH dime que quieres hacer", style="bold magenta", markdown=True)
        else:
            self.output_manager.print(f"\n\n# GEMINI SH", style="bold magenta", markdown=True)
            
    def init_model(self):
        """Inicializa el modelo y trae las funciones declaradas."""
        model_name = self.config_manager.config["MODEL_NAME"]
        max_output_tokens = self.config_manager.config["MODEL_MAX_OUTPUT_TOKENS"]
        safety_settings = self.config_manager.config["MODEL_SAFETY_SETTINGS"]
        system_instructions = self.state_manager.state["system_instructions"]
        functions_tools = Tool(function_declarations=self.function_manager.get_as_declarations())
        self.output_manager.debug(f"Model name: {model_name}")
        self.output_manager.debug(f"Function tools: {functions_tools}", 2)
        api_key = self.config_manager.get_api_key()
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name,
            generation_config=genai.GenerationConfig(max_output_tokens=max_output_tokens),
            tools=functions_tools,
            safety_settings=safety_settings,
            system_instruction=system_instructions
        )
        return model
            
    def generate_content(self, message):
        """Método para enviar un mensaje al modelo."""
        try:
            message_proto = self.message_to_proto(message)
            self.chat_manager.add_user_message(message)
            response = self.model.generate_content(message_proto)
            self.output_manager.debug(f"Gemini:\nResponse type: {type(response)}\nResponse: {response}", 2)
            return self.handle_gemini_response(response)
        except Exception as e:
            self.output_manager.debug(f"Error generating content: {e}")
            # TODO: Ask to retry
            return None
    
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
        self.output_manager.print("[bold blue]Gemini:[/bold blue]")
        for part in response_dict['candidates'][0]['content']['parts']:
            if 'text' in part:
                self.output_manager.print(part['text'], markdown=True)
            if 'function_call' in part and part['function_call']:
                function_call = part['function_call']
                function_name = function_call.get('name')
                function_arguments = function_call.get('args', {})
                self.output_manager.debug(f"Function name: {function_name}, Arguments: {function_arguments}")
                results = self.function_manager.execute_function(function_name, function_arguments)
                self.output_manager.debug(f"Function results: {results}")