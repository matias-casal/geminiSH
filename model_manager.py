"""
This module manages the interaction with the Google Gemini model.
"""

import os
import google.generativeai as genai
from google.ai.generativelanguage import Tool, Content, Part

DEBUG = os.environ.get("DEBUG", False)


class ModelManager:
    """
    The ModelManager class handles interactions with the Google Gemini model.
    
    Attributes:
        config_manager: Manages configuration settings.
        state_manager: Manages the state of the application.
        function_manager: Manages functions and their execution.
        output_manager: Manages output operations.
        input_manager: Manages user input.
        chat_manager: Manages chat interactions.
        model: The initialized Google Gemini model.
    """
    MODEL_PRESENTATION = "GEMINI SH"

    def __init__(
        self,
        config_manager,
        state_manager,
        function_manager,
        output_manager,
        input_manager,
        chat_manager,
    ):
        self.config_manager = config_manager
        self.state_manager = state_manager
        self.function_manager = function_manager
        self.output_manager = output_manager
        self.input_manager = input_manager
        self.chat_manager = chat_manager
        self.model = self.init_model()

    def first_message(self):
        """Method to send the first message to the model."""
        self.output_manager.print(
            f"\n\n# {self.MODEL_PRESENTATION}", style="bold bright_yellow", markdown=True
        )
        if self.state_manager.is_first_run():
            first_runs_path = os.path.join(
                self.config_manager.directory, "prompts", "first_runs.md"
            )
            if os.path.exists(first_runs_path):
                with open(first_runs_path, "r", encoding="utf-8") as f:
                    first_runs_text = f.read()
                    self.output_manager.print(first_runs_text, style="blue", markdown=True)

    def get_api_key(self):
        """Checks if the GOOGLE_API_KEY is set, if not, prompts the user to enter it."""
        if self.config_manager.config["GOOGLE_API_KEY"]:
            api_key = self.config_manager.config["GOOGLE_API_KEY"]
        elif os.environ.get("GOOGLE_API_KEY"):
            api_key = os.environ["GOOGLE_API_KEY"]
        else:
            self.output_manager.print(
                "API Key is not set. Please visit "
                "https://aistudio.google.com/app/apikey to obtain your API key.",
                style="bold red",
            )
            api_key = self.input_manager.input("Enter your GOOGLE_API_KEY: ")
        self.config_manager.config["GOOGLE_API_KEY"] = api_key
        return api_key

    def init_model(self):
        """Initializes the model and fetches the declared functions."""
        model_name = self.config_manager.config["MODEL_NAME"]
        # max_output_tokens = self.config_manager.config["MODEL_MAX_OUTPUT_TOKENS"]
        safety_settings = self.config_manager.config["MODEL_SAFETY_SETTINGS"]
        system_instructions = (
            self.state_manager.state["system_instructions"]
            + self.config_manager.get_system_information()
        )
        functions_tools = Tool(function_declarations=self.function_manager.get_as_declarations())
        self.output_manager.debug(f"Model name: {model_name}")
        api_key = self.get_api_key()
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name,
            # generation_config=genai.GenerationConfig(max_output_tokens=max_output_tokens),
            tools=functions_tools,
            safety_settings=safety_settings,
            system_instruction=system_instructions,
        )
        return model

    def generate_content(self):
        """Method to send a message to the model."""
        if DEBUG:
            for part in self.chat_manager.current_chat:
                self.output_manager.debug(f"Chat part: {part}", 2)
        try:
            with self.output_manager.managed_status("[bold blue]Gemini is thinking...[/bold blue]"):
                response = self.model.generate_content(self.chat_manager.current_chat)
            return self.handle_gemini_response(response)
        except Exception as e:
            self.output_manager.print(f"An error occurred: {e}", style="bold red")
            choice = self.input_manager.choose(
                "Do you want to retry?", choices=["yes", "no"], default="yes"
            )
            if choice == "yes":
                return self.generate_content()

    def message_to_proto(self, message):
        """Converts a message into a proto Content object."""
        if isinstance(message, str):
            return Content(role="user", parts=[Part(text=message)])

    def handle_gemini_response(self, response):
        """Handles the response from Google Gemini, extracting text and executing functions."""
        response_dict = type(response).to_dict(response)

        if not (
            response_dict.get("candidates")
            and response_dict["candidates"][0].get("content")
            and response_dict["candidates"][0]["content"].get("parts")
        ):
            self.output_manager.warning(
                "The model did not provide a response. If you upload files, "
                "they probably are not supported."
            )
            self.output_manager.debug(f"Model response: {response_dict}")
            return None

        function_responses = []
        for part in response_dict["candidates"][0]["content"]["parts"]:
            self.output_manager.debug(f"Part: {part}")
            try:
                if "text" in part:
                    self.output_manager.print(f"{part['text']}", style="blue", markdown=True)
                    part_text = part["text"].strip("\n")
                    self.chat_manager.add_text_part("model", f"{part_text}\n  ")

                if "function_call" in part and part["function_call"]:
                    self.output_manager.debug(f"Function call: {part['function_call']}")
                    with self.output_manager.managed_status(
                        "[yellow bold]Gemini is executing function...[/yellow bold]"
                    ):
                        function_call = part["function_call"]
                        function_name = function_call.get("name")
                        function_args = function_call.get("args", {})
                        self.output_manager.debug(
                            f"Function name: {function_name} | Function args: {function_args}"
                        )
                        self.chat_manager.add_function_call("model", function_name, function_args)
                        response = self.function_manager.execute_function(
                            function_name, function_args
                        )
                        function_responses.append((function_name, response))
            except Exception as e:
                print(e)

        for function_name, response in function_responses:
            self.handle_function_response(function_name, response)

    def handle_function_response(self, function_name, function_response):
        """
        Handles the response from a function call.

        Args:
            function_name (str): The name of the function that was called.
            function_response (Union[str, dict]): The response from the function call. 
                This can be a string or a dictionary containing the response data.

        Behavior:
            - If the function response is a string, it adds the response to the chat manager.
            - If the function response is a dictionary, it processes the response and 
              adds it to the chat manager. It also handles any additional responses 
              directed to the agent.
            - Finally, it triggers the generation of new content based on the function response.
        """
        if isinstance(function_response, str):
            self.chat_manager.add_function_response("user", function_name, function_response)
        elif isinstance(function_response, dict):
            if "response" in function_response:
                self.chat_manager.add_function_response(
                    "user", function_name, function_response["response"]
                )
            if "response_to_agent" in function_response:
                self.function_manager.handle_functions_response(
                    function_response["response_to_agent"]
                )
        self.generate_content()
