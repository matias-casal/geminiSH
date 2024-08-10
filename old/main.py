import argparse
import sys
import os
import time
import json
import re
import signal
import shutil
import requests
import traceback
import importlib.util
import platform
import asyncio
import inspect  
import mimetypes
from git import Repo
from shutil import copy
from pathlib import Path
from threading import Thread
from datetime import datetime, timedelta
from rich.live import Live
from rich.text import Text
from rich.console import Console
from pytimedinput import timedKey
from rich.markdown import Markdown
from rich.prompt import Prompt as ConsolePrompt
from prompt_toolkit import PromptSession, HTML
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.shortcuts import CompleteStyle
from typing import Callable
from google.protobuf import struct_pb2
from google.protobuf.json_format import MessageToDict
from google.protobuf.json_format import MessageToJson
import google.generativeai as genai
import google.api_core.exceptions
from google.protobuf.text_format import MessageToString
from google.ai.generativelanguage import (
    Content,
    Part,
    FileData,
    FunctionResponse,
    FunctionCall,
    FunctionDeclaration,
    Tool,
    Schema, 
    Type
)
from types import GenericAlias

DEBUG = os.getenv("DEBUG", False)
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-1.5-pro-latest")
CACHE_DIR = os.getenv("CACHE_DIR", "cache")
DATA_DIR = os.getenv("DATA_DIR", "data")
SYSTEM_DIR = os.getenv("SYSTEM_DIR", "system")
MAX_OUTPUT_TOKENS = os.getenv("MAX_OUTPUT_TOKENS", 4000)
SAVE_PROMPT_HISTORY = os.getenv("SAVE_PROMPT_HISTORY", True)
SAVE_OUTPUT_HISTORY = os.getenv("SAVE_OUTPUT_HISTORY", True)
FEEDBACK_TIMEOUT = int(os.getenv("FEEDBACK_TIMEOUT", 4))
MAX_TOKENS = 2097152
WARNING_THRESHOLD = 0.9
SUPPORTED_MIME_TYPES = [
    "text/plain",
    "application/pdf",
    "audio/mpeg",
    "audio/wav",
    "video/mp4",
    "image/jpeg",
    "image/png",
]

SAFETY_SETTINGS={
    'HATE': 'BLOCK_NONE',
    'HARASSMENT': 'BLOCK_NONE',
    'SEXUAL' : 'BLOCK_NONE',
    'DANGEROUS' : 'BLOCK_NONE'
}

console = Console()
session = PromptSession(
    history=InMemoryHistory(),
    auto_suggest=AutoSuggestFromHistory(),
    complete_style=CompleteStyle.READLINE_LIKE,
)

loaded_functions = []
uploaded_files = []
current_chat_id = None

#------------------------------------------------#
#            Chat Manager Class                  #
#------------------------------------------------#

class ChatManager:
    """Clase para gestionar la información de los chats."""

    def __init__(self, data_dir=DATA_DIR):
        global current_chat_id
        self.data_dir = data_dir
        self.chats_filepath = Path(self.data_dir) / "chats.json"
        self._ensure_data_dir_exists()
        self.current_chat_id = current_chat_id

    def _ensure_data_dir_exists(self):
        """Asegura que el directorio de datos existe."""
        Path(self.data_dir).mkdir(parents=True, exist_ok=True)
    
    def add_system_prompt(self, system_prompt):
        """Adds a system prompt to a chat."""

        chat_data = self.load_chat()
        if chat_data:
            # Convert Content object to dictionary before saving
            if isinstance(system_prompt, Content):
                system_prompt = Content.to_dict(system_prompt)

            chat_data["system_prompt"] = system_prompt
            self.save_chat(chat_data)  
        else:
            console.print(f"Error: No se encontró el chat {self.current_chat_id}", style="red")

    def _load_chats_data(self):
        """Loads chat data from chats.json."""
        if not self.chats_filepath.exists():
            return {}  # Return an empty dictionary if the file doesn't exist
        try:
            with open(self.chats_filepath, "r", encoding="utf-8") as f:
                chats_data = json.load(f)
                # Check if the loaded data is a dictionary
                if isinstance(chats_data, dict):
                    return chats_data
                else:
                    console.print(f"Error: Invalid data format in '{self.chats_filepath}'", style="bold red")
                    return {}  # Return an empty dictionary on invalid data format
        except json.JSONDecodeError as e:
            debug_print(f"Error loading chat data from '{self.chats_filepath}': {e}", function_name="_load_chats_data")
            return {}  #

    def add_file_to_chat(self, mime_type, uri, expiry_time, original_path):
        """Adds a file to the current chat."""
        chat_data = self.load_chat()
        if chat_data:
            if "files" not in chat_data:
                chat_data["files"] = []
            chat_data["files"].append({"mime_type": mime_type, "uri": uri, "expiry_time": expiry_time, "original_path": original_path})
            self.save_chat(chat_data)
        else:
            console.print(f"Error: No se encontró el chat {self.current_chat_id}", style="red")


    def _load_chats_data(self):
        """Loads chat data from chats.json."""
        if not self.chats_filepath.exists():
            return {}  # Return an empty dictionary if the file doesn't exist
        try:
            with open(self.chats_filepath, "r", encoding="utf-8") as f:
                chats_data = json.load(f)
                # Check if the loaded data is a dictionary
                if isinstance(chats_data, dict):
                    return chats_data
                else:
                    console.print(f"Error: Invalid data format in '{self.chats_filepath}'", style="bold red")
                    return {}  # Return an empty dictionary on invalid data format
        except json.JSONDecodeError as e:
            debug_print(f"Error loading chat data from '{self.chats_filepath}': {e}", function_name="_load_chats_data")
            return {}  # Return an empty dictionary on JSON decode error
    
    def _save_chats_data(self, chats_data):
        """Saves chat data to chats.json."""
        with open(self.chats_filepath, "w", encoding="utf-8") as f:
            json.dump(chats_data, f, indent=4)

    def save_chat(self, chat_data):  # Add chat_id as an argument
        """Saves chat data to chats.json using chat_id as key."""
        chats_data = self._load_chats_data()
        chats_data[self.current_chat_id] = chat_data  # Use the provided chat_id
        self._save_chats_data(chats_data)

    def load_chat(self):
        """Loads a specific chat by chat_id."""
        chats_data = self._load_chats_data()
        return chats_data.get(self.current_chat_id, None)  

    def create_chat(self):
        """Creates a new chat."""
        self.current_chat_id = str(int(time.time()))
        chat_data = {
            "turns": [],
            "created_at": datetime.now().isoformat()  # Guardar la fecha y hora de creación
        }
        chats_data = self._load_chats_data()
        chats_data[self.current_chat_id] = chat_data
        self._save_chats_data(chats_data)
        return self.current_chat_id

    def list_chats(self):
        """Lists the IDs of available chats."""
        chats_data = self._load_chats_data()
        sorted_chats = sorted(chats_data.values(),  # Iterate over values (chat data)
                              key=lambda x: datetime.fromisoformat(x['turns'][-1]['timestamp']) if x['turns'] else datetime.min,
                              reverse=True)
        return [chat['chat_id'] for chat in sorted_chats[:20]]

    def add_turn(self, role, content, function_calls=None, local_function_calls=None):
        """Adds a new turn to a chat."""
        chat_data = self.load_chat()
        if chat_data:
            new_turn = {
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat(),
            }
            if function_calls:
                new_turn["function_calls"] = function_calls
            if local_function_calls:
                new_turn["local_function_calls"] = local_function_calls
            chat_data["turns"].append(new_turn)
            self.save_chat(chat_data)  # Pass chat_id to save_chat
        else:
            console.print(f"Error: No se encontró el chat {self.current_chat_id}", style="red")

def debug_print(message, function_name: str = None, **kwargs):
    """Prints a debug message if DEBUG is True."""
    if DEBUG:
        function_prefix = f"[{function_name}] " if function_name else ""
        console.print(f"{function_prefix}{message}", style="yellow", **kwargs)

def _create_function_declaration(func: Callable) -> FunctionDeclaration:
    """Creates a FunctionDeclaration proto from a Python function."""

    # Extract function name and validate
    func_name = func.__name__
    if not re.match(r'^[a-zA-Z0-9_-]{1,63}$', func_name):
        raise ValueError(f"Invalid function name: {func_name}. Must be 1-63 characters long and contain only a-z, A-Z, 0-9, underscores, or dashes.")
    
    # Extract docstring
    func_doc = func.__doc__.strip() if func.__doc__ else "No description provided."
    
    # Extract parameters and create Schema
    func_signature = inspect.signature(func)
    properties = {}
    required = []
    for param_name, param in func_signature.parameters.items():
        param_type = _convert_python_type_to_proto_type(param.annotation)
        description = param.default.__doc__ if param.default != inspect._empty and hasattr(param.default, '__doc__') else "No description provided."
        properties[param_name] = param_type
        if param.default == inspect._empty:
            required.append(param_name)
    
    # Create FunctionDeclaration
    func_declaration = FunctionDeclaration(
        name=func_name,
        description=func_doc,
        parameters=Schema(
            type_=Type.OBJECT,
            properties=properties,
            required=required
        )
    )
    
    return func_declaration

def _convert_python_type_to_proto_type(python_type: Type) -> Type:
    """Converts a Python type to a corresponding proto Type."""
    # Extract the actual type from the tuple if necessary
    actual_type = python_type[1] if isinstance(python_type, tuple) else python_type

    if actual_type == str:
        return Schema(
            type_=Type.STRING
        )
    elif actual_type == int:
        return Schema(
            type_=Type.INTEGER)
    elif actual_type == float:
        
        return Schema(
            type_=Type.NUMBER
        )
    elif actual_type == bool:
        return Schema(
            type_=Type.BOOLEAN
            )
    elif isinstance(actual_type, GenericAlias):
        if actual_type.__origin__ is list:
            item_type = _convert_python_type_to_proto_type(actual_type.__args__[0])
            return Schema(
                type=Type.ARRAY,
                items=item_type
            )
        else:
            return Schema(
            type_=Type.ANY)  # Default to ANY for unsupported types
    else:
        return Schema(
            type_=Type.ANY)  # Default to ANY for unsupported types

        
def _load_functions_from_directory(directory=os.path.join("system", "functions")):
    """Loads custom functions from the specified directory and creates FunctionDeclaration protos."""
    global loaded_functions, geminiFunctions 
    loaded_functions = {func.name: func for func in geminiFunctions}
    for filename in os.listdir(directory):
        if filename.endswith(".py"):
            try:
                module_name = filename[:-3]
                module_path = os.path.join(directory, filename)
                spec = importlib.util.spec_from_file_location(module_name, module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                for func_name, func in module.__dict__.items():
                    # Check if it's a function AND not a class
                    if callable(func) and not func_name.startswith("__") and not inspect.isclass(func):
                        func_declaration = _create_function_declaration(func)
                        geminiFunctions.append(func_declaration)
                        loaded_functions[func_name] = func 
            except Exception as e:
                console.print(f"Error loading function '{func_name}' from '{filename}': {type(e).__name__} - {e}", style="bold red")
                
#------------------------------------------------#
#            Gemini Functions                    #
#------------------------------------------------#

def upload_file(file_path: str, expiry_time: str = None):
    """
    Handle a file by checking its MIME type and uploading it to Gemini if compatible.

    Parameters:
    file_path (str): The path to the file to handle.
    expiry_time (str): The expiration time for the file in ISO format. Defaults to 48 hours from now.

    Returns:
    str: A message indicating the result of the operation.
    """
    debug_print(f"\nUploading file: {file_path}", function_name="upload_file")
    global uploaded_files

    # Check the MIME type of the file
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type in SUPPORTED_MIME_TYPES:
        # Upload the file to Gemini
        with console.status(
            "[bold yellow]Uploading file..."
        ) as status:
            response = genai.upload_file(
                file_path
            )
        status.stop()
        # Agregar el archivo subido a la lista global
        uploaded_files.append(response)
        
        # Calcular la fecha de expiración si no se proporciona
        if not expiry_time:
            expiry_time = (datetime.now() + timedelta(hours=48)).isoformat()
        
        file_data = response.to_dict()
        # Guardar los datos del archivo en files.json
        file_data = {
            "file_uri": file_data.uri,
            "mime_type": file_data.mime_type,
            "expiry_time": expiry_time,
            "creation_time": datetime.now().isoformat(),
            "original_path": file_path
        }
        save_file_cache(file_data)
        
        # Agregar la información del archivo al chat actual
        chat_manager.add_file_to_chat(file_data["mime_type"], file_data["file_uri"], file_data["expiry_time"], file_data["original_path"])
        
        return f"File uploaded successfully: {response.uri}"
    else:
        return "Unsupported file type."

    
def save_file_cache(file_data):
    """Saves file data to cache."""
    files_path = Path(DATA_DIR) / "files.json"
    if not files_path.exists():
        files_path.parent.mkdir(parents=True, exist_ok=True)
        with open(files_path, "w", encoding="utf-8") as f:
            json.dump([], f)  # Create an empty list in the file

    files_data = _load_data(files_path)
    files_data.append(file_data)
    _save_data(files_data, files_path)
        

geminiFunctions = [
    _create_function_declaration(upload_file)
]

#------------------------------------------------#
#            Utility functions                  #
#------------------------------------------------#


def option_timer(
    instruction,
    responseOnTimeout=True,
    responseOnEnter=True,
    responseOnESC=False,
    timeout=FEEDBACK_TIMEOUT,
):
    """Handles timed user input for providing feedback."""
    user_input = [None]
    time_start = time.time()

    def wait_for_input(timeout):
        nonlocal user_input
        user_input[0], timed_out = timedKey(timeout=timeout)
        return not timed_out

    try:
        with console.status(
            f"[bold yellow]Continues in {int(timeout)} secs[/bold yellow] - {instruction}",
            spinner="dots",
        ) as status:
            input_thread = Thread(target=wait_for_input, args=[timeout])
            input_thread.daemon = True
            input_thread.start()
            while input_thread.is_alive():
                input_thread.join(timeout=0.1)
                remaining = timeout - (time.time() - time_start)
                status.update(
                    f"[bold yellow]Continues in {int(remaining)} secs[/bold yellow] - {instruction}"
                )
    except KeyboardInterrupt:
        _exit_program()
    finally:
        if input_thread.is_alive():
            input_thread.join()

    if user_input[0] == "\n":
        return responseOnEnter
    elif user_input[0] == "\x1b":
        return responseOnESC
    else:
        return responseOnTimeout


def _show_available_modes(previous_results, user_inputs):
    """Displays a list of available Gemini models."""
    for m in genai.list_models():
        if "generateContent" in m.supported_generation_methods:
            console.print(m.name)


def _show_help(previous_results, user_inputs):
    """Displays help information from INFO.md."""
    with open("INFO.md", "r", encoding="utf-8") as file:
        info_content = file.read()
    console.print(Markdown(info_content, justify="left"), style="italic light_coral")


def _exit_program():
    """Exits the program gracefully."""
    console.print("\n\nExiting program...", style="bold red")
    exit(0)


def _handle_sigint(signum, frame):
    """Handles SIGINT signal (Ctrl+C)."""
    _exit_program()


def _load_config():
    """Loads the configuration from rules.json."""
    with open(os.path.join(SYSTEM_DIR, "rules.json"), "r") as config_file:
        return json.load(config_file)


def handle_errors(func):
    """Decorator to handle unexpected errors."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            console.print(
                f"An unexpected error occurred, wanna try again?", style="red"
            )
            if DEBUG:
                console.print(e, traceback.format_exc(), style="bold red")
            console.print(
                "1. Retry\n2. Return to Main Menu\n3. Exit", style="bold yellow"
            )
            choice = ConsolePrompt.ask("Choose an option", choices=["1", "2", "3"])
            if choice == "1":
                return wrapper(*args, **kwargs)
            elif choice == "2":
                display_menu()
            elif choice == "3":
                _exit_program()
            return None

    return wrapper

def _check_api_key():
    """Checks if the GOOGLE_API_KEY is set, if not, prompts the user to enter it."""
    try:
        api_key = os.environ["GOOGLE_API_KEY"]
        console.print("API Key is set.", style="green")
    except KeyError:
        console.print(
            "API Key is not set. Please visit https://aistudio.google.com/app/apikey to obtain your API key.",
            style="bold red",
        )
        api_key = session.prompt("Enter your GOOGLE_API_KEY: ")
        os.environ["GOOGLE_API_KEY"] = api_key  # Set the API key in the environment variable
        genai.configure(api_key=api_key)

def _load_chat_history():
    """Loads chat history from cache."""
    global chat_history
    chats_filepath = Path(DATA_DIR) / "chats.json"

    # Ensure the 'data' directory exists
    if not chats_filepath.parent.exists():
        chats_filepath.parent.mkdir(parents=True, exist_ok=True)

    # Create an empty 'chats.json' if it doesn't exist
    if not chats_filepath.exists():
        with open(chats_filepath, "w", encoding="utf-8") as f:
            json.dump({}, f)  # Write an empty dictionary to the file
            return

    with open(chats_filepath, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            # Check if the loaded data is a dictionary
            if isinstance(data, dict):
                for chat_id, chat_data in data.items():
                    chat_history[chat_id] = chat_data.get('turns', [])  # Use .get() to handle missing 'turns' key
            else:
                console.print(f"Error: Invalid data format in '{chats_filepath}'. Expected a dictionary.", style="bold red")
        except Exception as e:
            debug_print(f"Error loading chat history from '{chats_filepath}': {e}", function_name="_load_chat_history")


#------------------------------------------------#
#          Data Management                      #
#------------------------------------------------#

def _save_data(data, filepath, indent=4):
    """Saves data to a JSON file."""
    filepath = Path(filepath)
    if not filepath.parent.exists():
        filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent)
        
def _load_data(filepath):
    """Loads data from a JSON file."""
    filepath = Path(filepath)
    if not filepath.parent.exists():
        filepath.parent.mkdir(parents=True, exist_ok=True)

    if not filepath.exists():
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump([], f)

    with open(filepath, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception as e:
            console.print(f"Error loading data from '{filepath}': {e}", style="bold red")
            return []


def save_file_cache(file_data):
    """Saves file data to cache."""
    _save_data(file_data, Path(DATA_DIR) / "files.json")

def load_file_cache(file_id):
    """Loads file data from cache by ID."""
    return next((file for file in _load_data(Path(DATA_DIR) / "files.json") if file['file_id'] == file_id), None)

def list_cached_files():
    """Lists the cached file IDs, sorted by creation time."""
    files_data = _load_data(Path(DATA_DIR) / "files.json")
    sorted_files = sorted(files_data, key=lambda x: x.get('creation_time'), reverse=True)[:20]
    return [file["file_id"] for file in sorted_files]

#------------------------------------------------#
#          Prompt and Response Handling         #
#------------------------------------------------#

def _format_prompt(prompt_name, previous_results_content, user_inputs_content):
    """Formats the prompt for Gemini, including base prompt, specific prompt and system info."""
    system_prompt = ""

    base_prompt_path = Path(SYSTEM_DIR) / "base_prompt.md"
    if base_prompt_path.exists():
        with open(base_prompt_path, "r", encoding="utf-8") as file:
            system_prompt = file.read()

    prompt_path = Path(SYSTEM_DIR) / "prompts" / f"{prompt_name}.md"
    if prompt_path.exists():
        with open(prompt_path, "r", encoding="utf-8") as file:
            system_prompt += file.read()

    system_info = f"Operating System: {platform.system()}, OS Version: {platform.version()}, Architecture: {platform.machine()}."
    system_prompt += f"\n\n{system_info}"

    prompt_content = Content(role="user", parts=[])

    if user_inputs_content:
        prompt_content.parts.extend(user_inputs_content.parts)
    if previous_results_content:
        prompt_content.parts.extend(previous_results_content.parts)

    system_prompt_content = Content(
        role="system", parts=[Part(text=system_prompt)]
    )

    debug_print(f"Prompt content: {prompt_content}", function_name="_format_prompt")
    return system_prompt_content, prompt_content

def _handle_response(
    response, output_format
):
    """Handles the response from the Gemini API, including formatting, saving history and token usage."""
    global current_chat_id, loaded_functions
    
    debug_print(f"Response received: { response }", function_name="_handle_response")
    try:
        response_dict = type(response).to_dict(response)
        debug_print(f"Response after conversion: {response_dict}", function_name="_handle_response")
    except Exception as e:
        console.print(f"Error converting protobuf to JSON: {e}", style="bold red")
        return None
    
    # Execute function calls immediately
    function_call_data = []
    extracted_text = ""
    if response_dict['candidates'] and response_dict['candidates'][0] and response_dict['candidates'][0]['content'] and response_dict['candidates'][0]['content']['parts']:
        for part in response_dict['candidates'][0]['content']['parts']:
            if 'text' in part: # Extrae el texto de la respuesta
                extracted_text += part['text']
            if 'function_call' in part and part['function_call']:
                function_call = part['function_call']
                debug_print(f"Function call detected: {function_call}", function_name="_handle_response")

                try:
                    function_name = function_call.get('name')
                    arguments = function_call.get('args', {})

                    debug_print(f"Function name: {function_name}, Arguments: {arguments}", function_name="_handle_response")
                except Exception as e:
                    console.print(f"Error converting protobuf to dictionary 1: {e}", style="bold red")
                    function_name = None
                    arguments = {}
                
                if function_name and function_name in loaded_functions:
                    function_to_call = loaded_functions[function_name]
                    debug_print(f"Calling function: {function_name} with arguments: {arguments}", function_name="_handle_response")
                    try:
                        # Execute the function
                        function_result = function_to_call(**arguments)
                        function_call_data.append({
                            'name': function_name,
                            'args': arguments,
                            'result': function_result
                        })
                        debug_print(f"Function {function_name} executed successfully. Result: {function_result}", function_name="_handle_response")
                    except Exception as e:
                        console.print(f"Error executing function '{function_name}': {e}", style="bold red")
                        function_call_data.append({
                            'name': function_name,
                            'args': arguments,
                            'error': str(e)
                        })
                else:
                    console.print(f"Function {function_name} not found", style="bold red")

    # Use extracted_text instead of response.text
    debug_print(f"Extracted text: {extracted_text}", function_name="_handle_response")
    if extracted_text:
        console.print("\nGemini Response:", style="bold green")
        console.print(Markdown(extracted_text))
    
    if SAVE_OUTPUT_HISTORY:
        debug_print(f"Saving handled response", function_name="_handle_response")
        chat_manager.add_turn(
            "model",
            extracted_text,
            function_call_data,
        )

    # If any function call was made, send the results to Gemini
    if function_call_data:
        debug_print(f"Sending function call results to Gemini", function_name="_handle_response")
        

    

@handle_errors
def _call_gemini_api(
    system_prompt_content: Content,
    prompt_content: Content,
    output_format: str = None,
    use_tools: bool = False,
):
    """Calls the Gemini API, handles function calls and token counting."""
    global current_chat_id, loaded_functions, uploaded_files
    try:
        with console.status(
            "[bold yellow]Waiting for Gemini..."
        ) as status:
            debug_print(f"Model name: {MODEL_NAME}", function_name="_call_gemini_api")
            debug_print(f"Prompt content parts: {prompt_content.parts}", function_name="_call_gemini_api")
            functions_tools = Tool(function_declarations=geminiFunctions)
            debug_print(f"Functions tools: {functions_tools}", function_name="_call_gemini_api")
            model = genai.GenerativeModel(
                MODEL_NAME,
                system_instruction=system_prompt_content.parts[0].text,
                generation_config=genai.GenerationConfig(max_output_tokens=MAX_OUTPUT_TOKENS),
                tools=functions_tools if use_tools else None,
                safety_settings=SAFETY_SETTINGS
            )

            debug_print(f"Loaded functions: {loaded_functions}", function_name="_call_gemini_api")

            chat_data = chat_manager.load_chat()

            if chat_data:
                conversation_history = chat_data['turns']
            else:
                conversation_history = []

            debug_print(f"Conversation history: {conversation_history}", function_name="_call_gemini_api")

            # Prepare the conversation history for generate_content
            conversation_history_content = []
            for turn in conversation_history:
                if 'content' in turn and turn['content'] != '':
                    conversation_history_content.append(Part(text=turn['content']))
                if 'function_calls' in turn:
                    for function_call in turn['function_calls']:
                        debug_print(f"Function call: {function_call}", function_name="_call_gemini_api")
                        
                        proto_struct_args = struct_pb2.Struct()
                        debug_print(f"Function call args: {function_call['args']}", function_name="_call_gemini_api")
                        proto_struct_args.update(function_call['args'])
                        debug_print(f"Proto struct args: {proto_struct_args}", function_name="_call_gemini_api")
                        conversation_history_content.append(
                            Part(function_call=FunctionCall(
                                name=function_call['name'],
                                args=proto_struct_args
                            ))
                        )
                        proto_struct_response = struct_pb2.Struct()
                        debug_print(f"Function call result: {function_call['result']}", function_name="_call_gemini_api")
                        proto_struct_response.update({"results": function_call['result']})
                        debug_print(f"Proto struct response: {proto_struct_response}", function_name="_call_gemini_api")
                        conversation_history_content.append(
                            Part(function_response=FunctionResponse(
                                name=function_call['name'],
                                response=proto_struct_response
                            ))
                        )

            debug_print(f"Conversation history content: {conversation_history_content}", function_name="_call_gemini_api")
            for part in conversation_history_content:
                debug_print(f"Part: {part}", function_name="_call_gemini_api")
                debug_print(f"Part type: {type(part)}", function_name="_call_gemini_api")
            # *** REALIZAR LA CUENTA DE TOKENS ANTES DE ENVIAR LA SOLICITUD ***
            token_count = 10#model.count_tokens(conversation_history_content).total_tokens

            if token_count > MAX_TOKENS:
                console.print(
                    f"Error: The prompt is too big, it has more than {MAX_TOKENS} tokens.",
                    style="bold red",
                )
                console.print(f"The prompt has {token_count} tokens", style="red")
                return None
            elif token_count > MAX_TOKENS * WARNING_THRESHOLD:
                console.print(
                    f"Warning: The prompt is using {token_count/MAX_TOKENS*100:.0f}% of the token limit. {token_count} tokens",
                    style="bold yellow",
                )
            else:
                console.print(f"The prompt has {token_count} tokens", style="green")

            # Obtener la respuesta de Gemini en modo streaming
            if isinstance(uploaded_files, list) and len(uploaded_files) > 0:
                debug_print(f"Uploaded files: {len(uploaded_files)}", function_name="_call_gemini_api")
                parts_with_files = []
                for file in uploaded_files:
                    file_dict = file.to_dict()
                    parts_with_files.append(Part(file_data=FileData(mime_type=file_dict['mime_type'], file_uri=file_dict['uri'])))
                parts_with_files.extend(conversation_history_content)  # Use extend instead of append
                response = model.generate_content(Content(role="user", parts=parts_with_files))
            else:
                response = model.generate_content(conversation_history_content)
            debug_print(f"Conversation history content: {conversation_history_content}", function_name="_call_gemini_api")
            
            status.stop()
            _handle_response(response, output_format)

    except google.api_core.exceptions.DeadlineExceeded:
        console.print(
            "Error: The request timed out. Please try again later.", style="bold red"
        )
        raise
    except google.api_core.exceptions.GoogleAPIError as e:
        console.print(f"API Error: {e.message}", style="bold red")
        raise
    except TypeError as e:
        console.print(f"Type Error: {e}", style="bold red")
        raise

def _handle_option(option):
    """Handles the execution of a selected menu option."""
    global current_chat_id
    results_content = Content()
    user_inputs_content = Content(role="user", parts=[])

    while True:
        if "inputs" in option:
            for input_detail in option["inputs"]:
                if input_detail.get("description"):
                    console.print(f"{input_detail['description']}", style="yellow")
                console.print(f"{input_detail['name']}:", style="bright_blue")
                user_input = session.prompt()
                user_inputs_content.parts.append(
                    {"text": user_input}
                )
                print(f"User input: {user_input}")
                if SAVE_OUTPUT_HISTORY:
                    chat_manager.add_turn('user', user_input)
        
        if option.get("output_format", "text") == "JSON":
            console.print(json.dumps(results_content, indent=4))
        else:
            text_to_display = ""
            if isinstance(results_content, Content):
                text_to_display = "".join([getattr(part, 'text', str(part)) for part in results_content.parts])
            elif isinstance(results_content, str):
                text_to_display = results_content
            else:
                text_to_display = str(results_content)
            console.print(Markdown(text_to_display))

        results_content = _handle_actions(option, results_content, user_inputs_content)
                
def _preprocess_json_response(data):
    """Preprocesses a JSON response from Gemini."""
    try:
        if isinstance(data, str):
            return json.loads(data)
        elif isinstance(data, (dict, list)):
            return data
        else:
            raise TypeError("Unsupported data type for JSON conversion")
    except json.JSONDecodeError as e:
        console.print(f"Error decoding JSON: {e}", style="bold red")
        return None
    except TypeError as e:
        console.print(f"Error: {e}", style="bold red")
        return None


def _execute_action(action, previous_results_content, user_inputs_content):
    """Executes a single action within an option, either a prompt or a function call."""
    global current_chat_id
    output_format = action.get("output_format", "text")
    use_tools = action.get("tools", False)
    debug_print(f"Action: {action}", function_name="_execute_action")
    if "prompt" in action:
        console.print(
            Markdown(f"\n\n# Processing prompt: {action['prompt']}"),
            style="bold bright_blue",
        )
        (
            system_prompt_content,
            prompt_content,
        ) = _format_prompt(action["prompt"], previous_results_content, user_inputs_content)
        debug_print(f"System prompt content: {system_prompt_content}", function_name="_execute_action")
        debug_print(f"Prompt content: {prompt_content}", function_name="_execute_action")
        if SAVE_OUTPUT_HISTORY:
            chat_manager.add_system_prompt(system_prompt_content.parts[0].text)
        return _call_gemini_api(
            system_prompt_content, prompt_content, output_format, use_tools
        )
    elif "function" in action:
        console.print(
            Markdown(f"\n\n# Executing action: {action['function']}"),
            style="bold bright_blue",
        )
        function_name = action["function"]
        if function_name in globals():
            function_to_call = globals()[function_name]
            if inspect.signature(function_to_call).parameters:
                return function_to_call(previous_results_content, user_inputs_content)
            else:
                return function_to_call()
            
        else:
            console.print(
                f"Function {function_name} is not defined", style="bold red"
            )
            return None
    return None

def _handle_response_chunks(model_response):
    """Handles streaming responses from Gemini."""
    full_response_text = ""
    live_text = Text()

    with Live(
        live_text, console=console, auto_refresh=True, transient=True
    ) as live:
        for chunk in model_response:
            text = getattr(
                chunk, "text", str(chunk) if isinstance(chunk, str) else None
            )
            if text is None:
                console.print(
                    f"Received non-text data: {chunk}", style="bold red"
                )
                continue

            full_response_text += text
            live_text.append(text)
            live.update(live_text)
        live.update(Text(""))
        live.stop()

    return full_response_text

#------------------------------------------------#
#          Core Interaction Logic               #
#------------------------------------------------#
@handle_errors
def _handle_actions(option, previous_results_content, user_inputs_content):
    """Handles the execution of actions within a menu option."""
    global current_chat_id
    debug_print(f"_handle_actions called with option: {option}", function_name="_handle_actions")
    debug_print(f"Previous results content: {previous_results_content}", function_name="_handle_actions")
    debug_print(f"User inputs content: {user_inputs_content}", function_name="_handle_actions")
    results_content = previous_results_content # Start with the content from the previous action

    for action in option["actions"]:
        debug_print(f"Processing action: {action}", function_name="_handle_actions")
        result_content = _execute_action(
            action, results_content, user_inputs_content
        )
        debug_print(f"Result processed actions: {result_content}", function_name="_handle_actions")
    return results_content

def _display_other_functions(options):
    """Displays other functions from menu_options.json."""
    console.print(Markdown(f"\n\n# Other Functions"), style="bold magenta")
    for index, option in enumerate(options, start=1):
        console.print(f"{index}. {option['description']}", style="bold blue")

    console.print(       f"{len(options) + 1}. Return to Main Menu", style="bold blue"
    )
    console.print(f"{len(options) + 2}. Exit Program", style="bold blue")

    choice = ConsolePrompt.ask(
        "Choose an option", choices=[str(i) for i in range(1, len(options) + 3)]
    )
    if int(choice) == len(options) + 1:
        display_menu()
        return
    elif int(choice) == len(options) + 2:
               _exit_program()
    else:
        selected_option = options[int(choice) - 1]
        _handle_option(selected_option)
        _display_other_functions(options)

#------------------------------------------------#
#          Menu Management                      #
#------------------------------------------------#
def _load_menu_options():
    """Loads menu options from menu_options.json."""
    with open(f"{SYSTEM_DIR}/menu_options.json", "r") as file:
        try:
            return json.load(file)
        except Exception as e:
            console.print(
                f"Error loading menu options:\n{e}", style="bold red"
            )
            _exit_program()

def display_menu():
    """Displays the main menu of the GeminiSH."""
    global current_chat_id 
    console.print(Markdown(f"\n\n# GEMINI SH"), style="bold magenta")
    options = _load_menu_options()
    main_menu_options = [
        opt
        for opt in options
        if opt.get("main_menu", False)
        and (
            not opt.get("debug_menu", False)
            or (opt.get("debug_menu", False) and DEBUG)
        )
    ]
    other_functions = [
        opt
        for opt in options
        if not opt.get("main_menu", False)
        and (
            not opt.get("debug_menu", False)
            or (opt.get("debug_menu", False) and DEBUG)
        )
    ]

    for index, option in enumerate(main_menu_options, start=1):
        console.print(f"{index}. {option['description']}", style="bold blue")

    console.print(
        f"{len(main_menu_options) + 1}. Other functions", style="bold blue"
    )
    console.print(
        f"{len(main_menu_options) + 2}. Exit program", style="bold blue"
    )

    choice = ConsolePrompt.ask(
        "Choose an option",
        choices=[str(i) for i in range(1, len(main_menu_options) + 3)],
    )
    if int(choice) == len(main_menu_options) + 1:
        _display_other_functions(other_functions)
    elif int(choice) == len(main_menu_options) + 2:
        _exit_program()
    else:
        selected_option = main_menu_options[int(choice) - 1]
        _handle_option(selected_option)

#------------------------------------------------#
#          Main and function calls               #
#------------------------------------------------#


def list_cached_documents():
    """Lists cached documents for user selection."""
    available_files = list_cached_files()
    if not available_files:
        console.print("No cached documents found.", style="yellow")
        return

    console.print(Markdown(f"\n\n# Available Cached Documents"), style="bold magenta")
    for index, file_id in enumerate(available_files, start=1):
        console.print(f"{index}. {file_id}", style="bold blue")

    console.print(f"{len(available_files) + 1}. Return to Main Menu", style="bold blue")

    choice = ConsolePrompt.ask(
        "Enter the number of the document to view (or press Enter to return to the main menu)",
        choices=[str(i) for i in range(1, len(available_files) + 2)],
        default=str(len(available_files) + 1),
    )
    if int(choice) == len(available_files) + 1:
        display_menu()
        return

    selected_index = int(choice) - 1
    file_id = available_files[selected_index]

    file_data = load_file_cache(file_id)
    if not file_data:
        console.print(f"Error: Could not load document {file_id}", style="red")
        return
    
    console.print(f"Viewing document {file_id}...", style="green")
    # Add logic to display the file content here
    console.print(file_data)

def recreate_data_file(previous_results, user_inputs):
    """Deletes and recreates the data.txt file in the cache."""
    data_txt_path = Path(CACHE_DIR) / "data.txt"
    if data_txt_path.exists():
        data_txt_path.unlink()
        console.print("The 'data.txt' file has been recreated.", style="green")
    else:
        console.print("The 'data.txt' file did not exist.", style="yellow")
    return None

async def _check_and_remove_expired_files():
    """Checks cached files for expiry and removes them from files.json."""
    files_filepath = Path(DATA_DIR) / "files.json"
    if files_filepath.exists():
        with open(files_filepath, "r", encoding="utf-8") as f:
            files_data = json.load(f)
        updated_files_data = []
        for file_data in files_data:
            # Verificar si el archivo ha expirado
            try:
                expiry_time = datetime.fromisoformat(file_data["expiry_time"])
                if expiry_time > datetime.now():
                    updated_files_data.append(file_data)
                else:
                    console.print(
                        f"Removing expired cached file: {file_data['file_id']}", style="yellow"
                    )
                    # Remove the actual file from the cache
                    # os.remove(file_data['file_path'])
            except KeyError:
                console.print(f"Warning: File {file_data['file_id']} does not have an expiry time. Skipping.", style="yellow")
                updated_files_data.append(file_data)  # Include the file even without an expiry time

        # Update files.json with the updated list
        with open(files_filepath, "w", encoding="utf-8") as f:
            json.dump(updated_files_data, f, indent=4)

def main():
    """Main function to handle command line arguments and direct program flow."""
    global chat_manager, current_chat_id
    try:
        chat_manager = ChatManager()  # Initialize ChatManager globally
        current_chat_id = chat_manager.create_chat()
        # Capture all the command line arguments
        arguments = sys.argv[1:]  # Exclude the script name
        # Combine all arguments into a single string
        combined_arguments = " ".join(arguments)
        # Start a separate thread to check for expired files
        asyncio.run(_check_and_remove_expired_files())
        _load_functions_from_directory()

        options = _load_menu_options()
        if combined_arguments == "menu":
            display_menu()
        else:
            selected_option = next(
                (opt for opt in options if opt["description"] == combined_arguments),
                options[0]  # Default to the first option if no match is found
            )
            _handle_option(selected_option)
    except KeyboardInterrupt:
        _exit_program()  # Call _exit_program when a keyboard interrupt is detected

def continue_chat():
    """Continúa una conversación cargando los turnos y archivos, y maneja archivos expirados."""
    chats_data = chat_manager._load_chats_data()
    if not chats_data:
        console.print("No hay conversaciones disponibles.", style="yellow")
        return

    # Mostrar lista de conversaciones disponibles
    console.print("Conversaciones disponibles:", style="bold blue")
    chat_list = []
    for idx, (chat_id, chat_data) in enumerate(chats_data.items(), start=1):
        created_at = datetime.fromisoformat(chat_data['created_at'])
        time_diff = datetime.now() - created_at
        console.print(f"{idx}. Chat ID: {chat_id} - Hace {time_diff.days} días, {time_diff.seconds // 3600} horas")
        chat_list.append(chat_id)

    # Seleccionar una conversación
    choice = ConsolePrompt.ask("Elige una conversación", choices=[str(i) for i in range(1, len(chat_list) + 1)])
    selected_chat_id = chat_list[int(choice) - 1]

    # Cargar la conversación seleccionada
    chat_data = chats_data[selected_chat_id]
    console.print(f"Cargando conversación {selected_chat_id}...", style="green")

    # Manejar archivos expirados
    if "files" in chat_data:
        for file in chat_data["files"]:
            expiry_time = datetime.fromisoformat(file["expiry_time"])
            if expiry_time < datetime.now():
                console.print(f"El archivo {file['original_path']} ha expirado.", style="yellow")
                reload_choice = ConsolePrompt.ask("¿Deseas volver a cargarlo?", choices=["yes", "no"])
                if reload_choice == "yes":
                    # Volver a cargar el archivo
                    result = upload_file(file["original_path"], file["expiry_time"])
                    console.print(result, style="green")
                    # Eliminar el archivo expirado
                    chat_data["files"].remove(file)
                    # Guardar la conversación actualizada
                    chat_manager.save_chat(chat_data)

    # Mostrar los turnos de la conversación
    for turn in chat_data["turns"]:
        console.print(f"{turn['role']}: {turn['content']}")


if __name__ == "__main__":
    # Set up the signal handler for SIGINT
    signal.signal(signal.SIGINT, _handle_sigint)
    _check_api_key()
    main()