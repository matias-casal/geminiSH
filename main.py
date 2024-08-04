# main.py
import argparse
import sys
import os
import time
import json
import signal
import shutil
import requests
import traceback
import importlib.util
import platform

from git import Repo
from shutil import copy
from pathlib import Path
from threading import Thread
from datetime import datetime
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

import google.generativeai as genai
import google.api_core.exceptions

from google.protobuf.json_format import MessageToDict
from google.ai.generativelanguage import (
    Content,
    Tool
)

DEBUG = os.getenv("DEBUG", False)
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-1.5-pro-latest")
CACHE_DIR = os.getenv("CACHE_DIR", "cache")
SYSTEM_DIR = os.getenv("SYSTEM_DIR", "system")
MAX_OUTPUT_TOKENS = os.getenv("MAX_OUTPUT_TOKENS", 4000)
SAVE_PROMPT_HISTORY = os.getenv("SAVE_PROMPT_HISTORY", True)
SAVE_OUTPUT_HISTORY = os.getenv("SAVE_OUTPUT_HISTORY", True)
FEEDBACK_TIMEOUT = int(os.getenv("FEEDBACK_TIMEOUT", 4))
MAX_TOKENS = 2097152
WARNING_THRESHOLD = 0.9

console = Console()
session = PromptSession(
    history=InMemoryHistory(),
    auto_suggest=AutoSuggestFromHistory(),
    complete_style=CompleteStyle.READLINE_LIKE,
)

loaded_functions = []
function_declarations = []
chat_history = {}


def option_timer(
    instruction,
    responseOnTimeout=True,
    responseOnEnter=True,
    responseOnESC=False,
    timeout=FEEDBACK_TIMEOUT,
):
    """Display a prompt with a countdown timer. Return True if the user presses Enter before the timer expires, otherwise return False."""
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

    if user_input[0] == "\n":  # ASCII code for the 'Enter' key
        return responseOnEnter
    elif user_input[0] == "\x1b":  # ASCII code for the 'Esc' key
        return responseOnESC
    else:
        return responseOnTimeout


def _show_available_modes(previous_results, user_inputs):
    """Displays available Gemini models."""
    for m in genai.list_models():
        if "generateContent" in m.supported_generation_methods:
            console.print(m.name)


def _show_help(previous_results, user_inputs):
    """Displays instructions on using the tool."""
    # Fetch the content of INFO.md from the root of the project and display it using Markdown
    with open("INFO.md", "r", encoding="utf-8") as file:
        info_content = file.read()
    console.print(Markdown(info_content, justify="left"), style="italic light_coral")


def _exit_program():
    """Exits the program gracefully."""
    console.print("\n\nExiting program...", style="bold red")
    exit(0)


def _handle_sigint(signum, frame):
    """Handles the SIGINT signal (Ctrl+C)."""
    _exit_program()


def _load_config():
    """Load configuration from a JSON file."""
    with open(os.path.join(SYSTEM_DIR, "rules.json"), "r") as config_file:
        return json.load(config_file)


def _update_data_txt(filename, content):
    """Updates the data.txt file with processed information from files."""
    data_txt_path = Path(CACHE_DIR) / "data.txt"
    filename = Path(filename).resolve()

    try:
        relative_path = filename.relative_to(Path.cwd())
        marker = f"```{relative_path}\n"
    except ValueError:
        console.print(f"Warning: Could not determine relative path for '{filename}'", style="yellow")
        marker = f"```{filename}\n"

    # Dividir el contenido en líneas y agregar el número de línea
    lines = content.splitlines()
    numbered_lines = [
        f"[LINE {i + 1}] {line}\n" for i, line in enumerate(lines)
    ]
    new_entry = f"{marker}{''.join(numbered_lines)}```\n"

    if data_txt_path.exists():
        with open(data_txt_path, "r+", encoding="utf-8") as file:
            existing_content = file.read()
            start_idx = existing_content.find(marker)
            if start_idx != -1:
                end_idx = existing_content.find(
                    "\n```", start_idx + len(marker))
                if end_idx == -1:
                    end_idx = len(existing_content)
                updated_content = existing_content[:start_idx] + \
                    new_entry + existing_content[end_idx:]
            else:
                updated_content = existing_content + new_entry
            file.seek(0)
            file.write(updated_content)
            file.truncate()
    else:
        with open(data_txt_path, 'w', encoding='utf-8') as file:
            file.write(new_entry)


def handle_errors(func):
    """Decorator to handle errors gracefully."""

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
                return wrapper(*args, **kwargs)  # Reintentar la función
            elif choice == "2":
                display_menu()  # Volver al menú principal
            elif choice == "3":
                _exit_program()  # Salir del programa
            return None

    return wrapper


def _check_api_key():
    """Check if the GOOGLE_API_KEY environment variable is set. If not, prompt the user to set it."""
    try:
        api_key = os.environ["GOOGLE_API_KEY"]
        console.print("API Key is set.", style="green")
    except KeyError:
        console.print(
            "API Key is not set. Please visit https://aistudio.google.com/app/apikey to obtain your API key.",
            style="bold red",
        )
        api_key = session.prompt("Enter your GOOGLE_API_KEY: ")
        genai.configure(api_key=api_key)


def _load_functions_from_directory(directory=os.path.join(SYSTEM_DIR, "functions")):
    """
    Load Python functions from a directory and create their declarations.
    The functions are loaded into the `loaded_functions` and `function_declarations` variables,
    and also added to the global scope.
    """
    global loaded_functions, function_declarations
    loaded_functions = []
    function_declarations = []
    for filename in os.listdir(directory):
        if filename.endswith(".py"):
            module_name = filename[:-3]  # Remove the '.py' from filename
            module_path = os.path.join(directory, filename)
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            # Create a custom namespace for the module to prevent imports from affecting globals
            module_namespace = {}
            # Load the module into the custom namespace
            # Temporarily add the module to sys.modules
            sys.modules[module_name] = module
            try:
                spec.loader.exec_module(module)
                # Copy only user-defined functions from the module to the namespace
                for func_name, func in module.__dict__.items():
                    if (
                        callable(func)
                        and not isinstance(func, type)
                        and not func_name.startswith("__")
                    ):
                        loaded_functions.append(func)
                        # Add function to custom namespace
                        module_namespace[func_name] = func
                        # Add function to global scope
                        globals()[func_name] = func
            finally:
                # Remove the module from sys.modules
                del sys.modules[module_name]


def _load_and_configure_model(system_prompt, output_format, use_tools):
    """Loads, configures, and returns a Gemini model."""
    global loaded_functions
    if use_tools:
        _load_functions_from_directory()

    generation_config = genai.GenerationConfig(max_output_tokens=MAX_OUTPUT_TOKENS)
    if output_format == "JSON":
        generation_config.response_mime_type = "application/json"
    # Pass loaded_functions directly to the model
    model = genai.GenerativeModel(
        MODEL_NAME,
        system_instruction=system_prompt,
        generation_config=generation_config,
        tools=loaded_functions,
    )
    return model


def _format_prompt(prompt_name, previous_results_content, user_inputs_content):
    """Formats the system and user prompts based on template and inputs."""
    system_prompt = ""
    attached_content = ""

    # Check if base_prompt.md exists and read it
    base_prompt_path = Path(SYSTEM_DIR) / "base_prompt.md"
    if base_prompt_path.exists():
        with open(base_prompt_path, "r", encoding="utf-8") as file:
            system_prompt = file.read()

    # Check if the specific prompt file exists and read it
    prompt_path = Path(SYSTEM_DIR) / "prompts" / f"{prompt_name}.md"
    if prompt_path.exists():
        with open(prompt_path, "r", encoding="utf-8") as file:
            system_prompt += file.read()

    # Add system information to the system prompt
    system_info = f"Operating System: {platform.system()}, OS Version: {platform.version()}, Architecture: {platform.machine()}."
    system_prompt += f"\n\n{system_info}"

    # Check if data.txt exists and read it
    data_txt_path = Path(CACHE_DIR) / "data.txt"
    if data_txt_path.exists():
        with open(data_txt_path, "r", encoding="utf-8") as file:
            attached_content = file.read()

    # Initialize prompt_content with an empty list of parts
    prompt_content = Content(role="user", parts=[])

    # Build the complete prompt with all sections
    # Convert user_inputs and previous_results to protos.Content
    if user_inputs_content:
        prompt_content.parts.extend(user_inputs_content.parts)
    if previous_results_content:
        prompt_content.parts.extend(previous_results_content.parts)
    if attached_content:
        prompt_content.parts.append(
            {"text": f"\n\n```ATTACHED DATA SECTION:\n{attached_content}\n```"}
        )

    # Incorporate system prompt into a Content object
    system_prompt_content = Content(
        role="system", parts=[{"text": system_prompt}])

    if DEBUG:
        console.print("prompt", prompt_content, style="yellow")
    return system_prompt_content, prompt_content


def _handle_response(response, output_format, system_prompt_content, use_tools=False):
    """Handles the response from Gemini, including function calls."""
    full_text_response, full_actions_response = _handle_function_call(response, output_format)

    if DEBUG:
        console.print("\nResponse parts:", style="yellow")
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'text'):
                console.print(f"Text: {part.text}", style="yellow")
            elif hasattr(part, 'function_call'):
                console.print(f"Function call: {part.function_call.name}", style="yellow")
                console.print(f"Arguments: {part.function_call.args}", style="yellow")
            else:
                console.print(f"Unknown part type: {type(part)}", style="yellow")

    # Imprimir la respuesta de texto
    if full_text_response:
        console.print("\nRespuesta del modelo:", style="bold green")
        console.print(Markdown(full_text_response))

    # Save output history if enabled
    if SAVE_OUTPUT_HISTORY:
        _save_output_history(
            full_text_response,
            full_actions_response,
            response.candidates[0].content,
            system_prompt_content,
        )

    return full_text_response


def _load_chat_history():
    """Load chat history from cached files."""
    global chat_history
    cache_path = Path("cache")
    outputs_path = cache_path / "outputs_history"

    # Load prompts and outputs from files
    if outputs_path.exists():
        for filename in outputs_path.glob("*.json"):
            with open(filename, "r", encoding="utf-8") as f:
                try:
                    output_content = json.load(f)
                    # Check if response exists and is not empty
                    if 'response' in output_content and output_content['response']['text']:
                        prompt_text = output_content['prompt']['text']
                        response_text = output_content['response']['text']
                        chat_history[prompt_text] = response_text
                except Exception as e:
                    console.print(f"Error loading chat history from '{filename}': {e}", style="bold red")


def _save_output_history(text_response, actions_response, prompt_content, system_prompt_content):
    """Saves the current output, prompt, and system prompt to a file in the cache."""
    global chat_history
    cache_path = Path("cache")
    outputs_path = cache_path / "outputs_history"
    outputs_path.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_filename = outputs_path / f"{timestamp}.json"

    # Extraer el texto de las partes del prompt_content
    prompt_text = "".join([part.text if hasattr(part, 'text') else str(part) for part in prompt_content.parts])

    # Extraer el texto de las partes del system_prompt_content
    system_prompt_text = "".join([part.text if hasattr(part, 'text') else str(part) for part in system_prompt_content.parts])

    # Create a dictionary to store the information
    output_content = {
        'response': {
            'text': text_response,
            'actions': actions_response,
        },
        'prompt': {
            'text': prompt_text,
            'system': system_prompt_text
        }
    }

    # Save the dictionary as a JSON file
    with open(output_filename, "w", encoding="utf-8") as file:
        json.dump(output_content, file, indent=4)

    # Adds current conversation to chat_history
    chat_history[prompt_text] = text_response


def _handle_function_call(response, output_format):
    """Processes function calls in the Gemini response and returns text and action responses."""
    full_actions_response = ""
    full_text_response = ""
    # Extract function calls
    function_calls = [
        part.function_call
        for part in response.candidates[0].content.parts
        if hasattr(part, 'function_call')
    ]

    # Execute collected function calls
    for func_call in function_calls:
        func_name = func_call.name
        args = MessageToDict(func_call.args) if func_call.args else {}  # Handle cases where args are not provided
        # Check if the function exists in the global scope before calling it
        if func_name in globals():
            try:
                function_to_call = globals()[func_name]
                result = function_to_call(**args)
                # Assuming 'result' is a string for now
                full_actions_response += f"- function_name: {func_name} - function_response: {result}\n"
                full_text_response += result
            except Exception as e:
                console.print(
                    f"Error executing function {func_name}: {str(e)}", style="bold red"
                )
        else:
            if func_name:
                console.print(
                    f"Function {func_name} is not defined", style="bold red"
                )

    if output_format == "JSON":
        full_text_response = _preprocess_json_response(full_text_response)
    return full_text_response, full_actions_response


@handle_errors
def _call_gemini_api(
    system_prompt_content: Content,
    prompt_content: Content,
    output_format: str = None,
    use_tools: bool = False,
    chat_id: str = None,  # New parameter for chat ID
):
    """Calls the Gemini API with the provided prompts and configuration."""
    try:
        with console.status(
            "[bold yellow]Waiting for Gemini..."
        ) as status:
            if DEBUG:
                console.print("\n-- Model name:", MODEL_NAME, style="yellow")

            model = _load_and_configure_model(
                system_prompt_content.parts[0].text, output_format, use_tools
            )
            console.print("\n-- Loaded functions:", loaded_functions, style="yellow")
            cache_path = Path("cache")

            # Check if the cache directory exists, if not, create it
            cache_path.mkdir(exist_ok=True)

            if SAVE_PROMPT_HISTORY:
                _save_prompt_history(prompt_content, system_prompt_content)

            # Initialize full_actions_response before the function call loop
            full_actions_response = ""

            # Load existing chat data if chat_id is provided
            chat_data = load_chat(chat_id) if chat_id else None

            # Execute collected function calls
            if use_tools:
                function_calls = []  # Array to store function calls

                # Extract function calls from the prompt_content
                for part in prompt_content.parts:
                    if hasattr(part, 'function_call') and hasattr(part.function_call, 'name'):
                        function_calls.append(part.function_call)

                for func_call in function_calls:
                    func_name = func_call.name
                    args = getattr(func_call, 'args', {})
                    # Check if the function exists in the global scope before calling it
                    if func_name in globals():
                        if DEBUG:
                            console.print(
                                f"Calling function {func_name} with args {args}", style="blue italic")
                        function_to_call = globals()[func_name]
                        result = function_to_call(**args)
                        if DEBUG:
                            console.print(
                                f"Function returned: {result}\n", style="blue italic")
                        # Update this line to handle the new return type (File object)
                        full_actions_response += f"- function_name: {func_name} - function_response: {result.name if hasattr(result, 'name') else result}\n"
                        # Add the uploaded file to the prompt using its URI
                        if isinstance(result, genai.types.File):
                            # Prepare FileData object
                            file_data = {
                                "mime_type": result.mime_type,
                                "file_uri": result.uri
                            }
                            # Add the uploaded file to the prompt
                            prompt_content.parts.append({"file": file_data})  # changed text to file
                            if DEBUG:
                                console.print(
                                    f"Prompt: {prompt_content}", style="blue italic")
            # Extraer el texto del prompt_content
            prompt_text = "".join([part.text if hasattr(part, 'text') else str(part) for part in prompt_content.parts])

            if DEBUG and prompt_text in chat_history:
                console.print("Loading response from cache...", style="yellow")
                full_text_response = chat_history[prompt_text]
                status.stop()
                # Create a new Content object with the cached response
                return Content(role="assistant", parts=[{"text": full_text_response}])
            else:
                # Execute collected function calls
                if use_tools:
                    function_calls = []  # Array to store function calls

                    # Extract function calls from the prompt_content
                    for part in prompt_content.parts:
                        if hasattr(part, 'function_call') and hasattr(part.function_call, 'name'):
                            function_calls.append(part.function_call)

                    for func_call in function_calls:
                        func_name = func_call.name
                        args = getattr(func_call, 'args', {})
                        # Check if the function exists in the global scope before calling it
                        if func_name in globals():
                            try:
                                if DEBUG:
                                    console.print(
                                        f"Calling function {func_name} with args {args}", style="blue italic")
                                function_to_call = globals()[func_name]
                                result = function_to_call(**args)
                                if DEBUG:
                                    console.print(
                                        f"Function returned: {result}\n", style="blue italic")
                                # Update this line to handle the new return type (File object)
                                full_actions_response += f"- function_name: {func_name} - function_response: {result.name if hasattr(result, 'name') else result}\n"
                                # Add the uploaded file to the prompt using its URI
                                if isinstance(result, genai.types.File):
                                    # Prepare FileData object
                                    file_data = {
                                        "mime_type": result.mime_type,
                                        "file_uri": result.uri
                                    }
                                    # Add the uploaded file to the prompt
                                    prompt_content.parts.append({"text": f"\n\nDescribe this image: {file_data}"})
                                    if DEBUG:
                                        console.print(
                                            f"Prompt: {prompt_content}", style="blue italic")
                            except Exception as e:
                                console.print(
                                    f"Error executing function {func_name}: {str(e)}", style="bold red")
                        else:
                            if func_name:
                                console.print(
                                    f"Function {func_name} is not defined", style="bold red")

                # Only now, after processing function calls, send the prompt to Gemini
                chat = model.start_chat(enable_automatic_function_calling=use_tools)
                response = chat.send_message(prompt_content)

                total_content = Content()
                total_content.parts.extend(system_prompt_content.parts)
                total_content.parts.extend(prompt_content.parts)
                token_count = model.count_tokens(total_content).total_tokens

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

                status.stop()

                # Handle response chunks and return the full content
                return _handle_response(response, output_format, system_prompt_content, use_tools)
    except google.api_core.exceptions.DeadlineExceeded:
        console.print(
            "Error: The request timed out. Please try again later.", style="bold red"
        )
        raise
    except google.api_core.exceptions.GoogleAPIError as e:
        console.print(f"API Error: {e.message}", style="bold red")
        raise

def _save_prompt_history(prompt_content, system_prompt_content):
    """Saves the current prompt and system prompt to a file in the cache."""
    cache_path = Path("cache")
    prompts_path = cache_path / "prompts_history"
    prompts_path.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    prompt_filename = prompts_path / f"{timestamp}.json"

    # Ensure prompt_content and system_prompt_content are iterable
    prompt_text = "".join([part.text for part in prompt_content.parts])
    system_prompt_text = "".join([part.text for part in system_prompt_content.parts])

    # Create a dictionary to store the information
    prompt_content_dict = {
        'prompt': {
            'text': prompt_text,
            'system': system_prompt_text
        }
    }

    # Save the dictionary as a JSON file
    with open(prompt_filename, "w", encoding="utf-8") as file:
        json.dump(prompt_content_dict, file, indent=4)


def _handle_response_chunks(model_response):
    """Handles streaming responses from the Gemini model."""
    full_response_text = ""
    live_text = Text()

    # Use Live to display the text as it arrives
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

            # Accumulate text in the full text response
            full_response_text += text
            # Update the text in the Live display
            live_text.append(text)
            live.update(live_text)
        live.update(Text(""))
        live.stop()

    return full_response_text


def _preprocess_json_response(data):
    """Preprocesses JSON responses for parsing or conversion."""
    try:
        if isinstance(data, str):
            # Attempt to load the string as JSON
            response_json = json.loads(data)
            return response_json  # Return the deserialized JSON object
        elif isinstance(data, (dict, list)):
            return data  # Return the JSON string
        else:
            raise TypeError("Unsupported data type for JSON conversion")
    except json.JSONDecodeError as e:
        console.print(f"Error decoding JSON: {e}", style="bold red")
        return None
    except TypeError as e:
        console.print(f"Error: {e}", style="bold red")
        return None


def _handle_user_feedback(user_inputs_content, directly=False):
    """Collects and appends user feedback to the content."""
    feedback = directly or option_timer(
        "[red]Press ESC to continues[/red] - [green]Press Enter to add feedback[/green]",
        responseOnTimeout=False,
    )
    if feedback:
        user_feedback = session.prompt(
            HTML("<yellow><bold><italic>Provide feedback</italic></bold></yellow> ")
        )
        if user_feedback:
            user_inputs_content.parts.append(
                {"text": f"[user_feedback]{user_feedback}[/user_feedback]"}
            )
    return user_inputs_content


def _execute_action(action, previous_results_content, user_inputs_content):
    """Executes the specified action, either calling the Gemini API or a function."""
    output_format = action.get("output_format", "text")
    use_tools = action.get("tools", False)

    if "prompt" in action:
        console.print(
            Markdown(f"\n\n# Processing prompt: {action['prompt']}"),
            style="bold bright_blue",
        )
        (
            system_prompt_content,
            prompt_content,
        ) = _format_prompt(action["prompt"], previous_results_content, user_inputs_content)
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
            return function_to_call(previous_results_content, user_inputs_content)
        else:
            console.print(
                f"Function {function_name} is not defined", style="bold red"
            )
            return None
    return None


def _handle_actions(option, previous_results_content, user_inputs_content):
    """Handles user interactions and action execution."""
    # Handle actions
    if "actions" in option:
        while True:
            for action in option["actions"]:
                result_content = _handle_action(
                    action, previous_results_content, user_inputs_content
                )
                if result_content is not None:
                    results_content = result_content
            not_continue = option_timer(
                "[red]Press ESC to abort[/red] - [green]Press Enter add feedback[/green]",
                responseOnTimeout=True,
                responseOnEnter="feedback",
            )
            if not_continue == "feedback":
                user_inputs_content = _handle_user_feedback(
                    user_inputs_content, directly=True
                )
            if not not_continue:
                break
        return results_content
    else:
        console.print(
            "This option does not have any actions defined yet. Please try another option.",
            style="yellow",
        )
        # Prompt for new input instead of starting the timer
        display_menu()
        return None


def _handle_action(action, previous_results_content, user_inputs_content):
    """Handles user interactions and action execution."""
    # Capture user feedback with a 2-second timeout only for 'prompt' actions
    if "prompt" in action and "pre_feedback" in action:
        user_inputs_content = _handle_user_feedback(user_inputs_content)
    # Execute action
    result_content = _execute_action(
        action, previous_results_content, user_inputs_content
    )

    return result_content


def _display_other_functions(options):
    """Displays other available functions from the menu options."""
    console.print(Markdown(f"\n\n# Other Functions"), style="bold magenta")
    for index, option in enumerate(options, start=1):
        console.print(f"{index}. {option['description']}", style="bold blue")

    console.print(f"{len(options) + 1}. Return to Main Menu", style="bold blue")
    console.print(f"{len(options) + 2}. Exit Program", style="bold blue")

    choice = ConsolePrompt.ask(
        "Choose an option", choices=[str(i) for i in range(1, len(options) + 3)]
    )
    if int(choice) == len(options) + 1:
        display_menu()
        return
    elif int(choice) == len(options) + 2:
        _exit_program()  # Sale del programa
    else:
        selected_option = options[int(choice) - 1]
        _handle_option(selected_option)
        # Repite el menú después de ejecutar una acción
        _display_other_functions(options)


def _load_menu_options():
    """Loads menu options from the JSON configuration file."""
    with open(f"{SYSTEM_DIR}/menu_options.json", "r") as file:
        try:
            return json.load(file)
        except Exception as e:
            console.print(
                f"Error loading menu options:\n{e}", style="bold red"
            )
            _exit_program()

#-------------------------------------------#
#    New functions for chat management     #
#-------------------------------------------#

def save_chat(chat_data):
    """Guarda la información del chat en un archivo JSON."""
    chats_dir = Path(CACHE_DIR) / "chats"
    chats_dir.mkdir(exist_ok=True)
    chat_filepath = chats_dir / f"{chat_data['chat_id']}.json"
    with open(chat_filepath, "w", encoding="utf-8") as f:
        json.dump(chat_data, f, indent=4)


def load_chat(chat_id):
    """Carga la información del chat con el ID especificado."""
    chat_filepath = Path(CACHE_DIR) / "chats" / f"{chat_id}.json"
    if chat_filepath.exists():
        with open(chat_filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return None


def list_chats():
    """Devuelve una lista de los IDs de los 20 chats más recientes."""
    chats_dir = Path(CACHE_DIR) / "chats"
    chat_files = list(chats_dir.glob("*.json")) if chats_dir.exists() else []
    chat_files.sort(key=os.path.getmtime, reverse=True)
    return [Path(chat_file).stem for chat_file in chat_files[:20]]


#-------------------------------------------#
# New functions for cached file management  #
#-------------------------------------------#

def save_file_cache(file_data):
    """Guarda la información del archivo en caché en el archivo JSON."""
    files_dir = Path(CACHE_DIR) / "files"
    files_dir.mkdir(exist_ok=True)
    file_filepath = files_dir / f"{file_data['file_id']}.json"
    with open(file_filepath, "w", encoding="utf-8") as f:
        json.dump(file_data, f, indent=4)


def load_file_cache(file_id):
    """Carga la información del archivo en caché con el ID especificado."""
    file_filepath = Path(CACHE_DIR) / "files" / f"{file_id}.json"
    if file_filepath.exists():
        with open(file_filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return None

def list_cached_files():
    """Devuelve una lista de los IDs de los 20 archivos en caché más recientes."""
    files_dir = Path(CACHE_DIR) / "files"
    file_files = list(files_dir.glob("*.json")) if files_dir.exists() else []
    file_files.sort(key=os.path.getmtime, reverse=True)
    return [Path(file_file).stem for file_file in file_files[:20]]

def display_menu():
    """Displays the main menu of the GeminiSH."""
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


def _handle_option(option):
    """Handles user interaction, action execution, and feedback collection for a menu option."""
    user_inputs_content = Content(role="user", parts=[])
    if "inputs" in option:
        for input_detail in option["inputs"]:
            console.print(f"{input_detail['description']}", style="yellow")
            user_input = session.prompt()
            user_inputs_content.parts.append(
                {"text": f"[{input_detail['name']}]{user_input}[/{input_detail['name']}]"}
            )

    results_content = Content(role="assistant", parts=[])

    # Handle actions
    results_content = _handle_actions(
        option, results_content, user_inputs_content
    )

    if results_content is not None:
        # Display the response, handling Markdown and JSON formatting
        if option.get("output_format", "text") == "JSON":
            console.print(json.dumps(results_content, indent=4))
        else:
            # Extract text from the parts of the Content object
            text_to_display = ""
            if isinstance(results_content, Content):
                text_to_display = "".join([getattr(part, 'text', str(part)) for part in results_content.parts])
            elif isinstance(results_content, str):
                text_to_display = results_content
            else:
                text_to_display = str(results_content)
            console.print(Markdown(text_to_display))

        # Ask for feedback and display response
        not_continue = option_timer(
            "[red]Press ESC to continues[/red] - [green]Press Enter to add feedback[/green]",
            responseOnTimeout=False,
        )
        if not_continue:
            user_inputs_content = _handle_user_feedback(
                user_inputs_content, directly=True
            )
        # Repite el menú después de ejecutar una acción
        display_menu()

#------------------------------------------------#
#          Main and function calls               #
#------------------------------------------------#

def continue_chat(previous_results_content, user_inputs_content):
    """Handles continuation of previous conversations."""
    available_chats = list_chats()
    if not available_chats:
        console.print("No se encontraron conversaciones previas.", style="yellow")
        # Volver al menú principal
        display_menu()
        return

    # User selects from recent chat IDs
    console.print(Markdown(f"\n\n# Recent Conversations"), style="bold magenta")
    for index, chat_id in enumerate(available_chats, start=1):
        console.print(f"{index}. {chat_id}", style="bold blue")

    choice = ConsolePrompt.ask(
        "Enter the number of the conversation to continue (or press Enter to return to the main menu)",
        choices=[str(i) for i in range(1, len(available_chats) + 1)] + [""],
        default="",
    )
    if not choice:
        display_menu()
        return

    selected_index = int(choice) - 1
    chat_id = available_chats[selected_index]

    chat_data = load_chat(chat_id)
    if not chat_data:
        console.print(f"Error: Could not load chat {chat_id}", style="red")
        return

    console.print(f"Continuing conversation {chat_id}...", style="green")
    # Add logic to continue the chat here, using chat_data
    
    # You might want to use previous_results_content and user_inputs_content here
    # For example:
    # user_inputs_content.parts.append({"text": f"Continuing chat {chat_id}"})
    # results_content = _handle_actions(chat_data, previous_results_content, user_inputs_content)
    
    # Return to main menu after continuing the chat
    display_menu()

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

    console.print(f"Viewing document {file_id}...", style="green")
    # Add logic to display the file content here

def use_cached_document():
    """Handles the use of cached documents in the prompt."""
    available_files = list_cached_files()
    if not available_files:
        console.print("No cached documents found.", style="yellow")
        return
    
    console.print(Markdown(f"\n\n# Available Cached Documents"), style="bold magenta")
    for index, file_id in enumerate(available_files, start=1):
        console.print(f"{index}. {file_id}", style="bold blue")

    console.print(f"{len(available_files) + 1}. Return to Main Menu", style="bold blue")

    choice = ConsolePrompt.ask(
        "Enter the number of the document to use (or press Enter to return to the main menu)",
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

    console.print(f"Using document {file_id} in the prompt...", style="green")
    # Add logic to use file_data in the prompt here,
    # such as adding the file to the content.parts list.

def main():
    """Main function to handle command line arguments and direct program flow."""
    try:
        if DEBUG:
            console.print("Loading chat history...", style="yellow")
            _load_chat_history()  # Loads chat history from cache on startup
        display_menu()  # Display the menu if no input is provided
    except KeyboardInterrupt:
        _exit_program()  # Call _exit_program when a keyboard interrupt is detected
        
if __name__ == "__main__":
    # Set up the signal handler for SIGINT
    signal.signal(signal.SIGINT, _handle_sigint)
    _check_api_key()
    main()