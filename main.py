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
import asyncio
import inspect  
import mimetypes
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

console = Console()
session = PromptSession(
    history=InMemoryHistory(),
    auto_suggest=AutoSuggestFromHistory(),
    complete_style=CompleteStyle.READLINE_LIKE,
)

loaded_functions = []
function_declarations = []
chat_history = {}
current_chat_id = None


def option_timer(
    instruction,
    responseOnTimeout=True,
    responseOnEnter=True,
    responseOnESC=False,
    timeout=FEEDBACK_TIMEOUT,
):
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
    for m in genai.list_models():
        if "generateContent" in m.supported_generation_methods:
            console.print(m.name)


def _show_help(previous_results, user_inputs):
    with open("INFO.md", "r", encoding="utf-8") as file:
        info_content = file.read()
    console.print(Markdown(info_content, justify="left"), style="italic light_coral")


def _exit_program():
    console.print("\n\nExiting program...", style="bold red")
    exit(0)


def _handle_sigint(signum, frame):
    _exit_program()


def _load_config():
    with open(os.path.join(SYSTEM_DIR, "rules.json"), "r") as config_file:
        return json.load(config_file)


def handle_errors(func):
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
    global loaded_functions, function_declarations
    loaded_functions = []
    function_declarations = []
    for filename in os.listdir(directory):
        if filename.endswith(".py"):
            module_name = filename[:-3]
            module_path = os.path.join(directory, filename)
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            module_namespace = {}
            sys.modules[module_name] = module
            try:
                spec.loader.exec_module(module)
                for func_name, func in module.__dict__.items():
                    if (
                        callable(func)
                        and not isinstance(func, type)
                        and not func_name.startswith("__")
                    ):
                        loaded_functions.append(func)
                        module_namespace[func_name] = func
                        globals()[func_name] = func
            finally:
                del sys.modules[module_name]


def _load_and_configure_model(system_prompt, output_format, use_tools):
    global loaded_functions
    if use_tools:
        _load_functions_from_directory()

    generation_config = genai.GenerationConfig(max_output_tokens=MAX_OUTPUT_TOKENS)
    if output_format == "JSON":
        generation_config.response_mime_type = "application/json"
    model = genai.GenerativeModel(
        MODEL_NAME,
        system_instruction=system_prompt,
        generation_config=generation_config,
        tools=loaded_functions,
    )
    return model


def _format_prompt(prompt_name, previous_results_content, user_inputs_content):
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
        role="system", parts=[{"text": system_prompt}])

    if DEBUG:
        console.print("prompt", prompt_content, style="yellow")
    return system_prompt_content, prompt_content

def _handle_response(
    response, output_format, system_prompt_content, use_tools=False, function_calls=None, local_function_calls=None
):
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

    if response.text and (output_format == "JSON" or DEBUG):
        console.print("\nRespuesta del modelo:", style="bold green")
        console.print(Markdown(response.text))

    if SAVE_OUTPUT_HISTORY:
        _save_output_history(
            response.text,
            function_calls,
            response.candidates[0].content,
            system_prompt_content,
            local_function_calls, # New parameter to store local function calls
        )

    return response.candidates[0].content 

def _load_chat_history():
    global chat_history
    chats_filepath = Path(DATA_DIR) / "chats.json"

    if not chats_filepath.parent.exists():
        chats_filepath.parent.mkdir(parents=True, exist_ok=True)

    if not chats_filepath.exists():
        with open(chats_filepath, "w", encoding="utf-8") as f:
            json.dump([], f)

    with open(chats_filepath, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            if not data:
                return
            for chat in data:
                prompt_text = ""
                for turn in chat['turns']:
                    if turn['role'] == 'user':
                        prompt_text += turn['content']
                if prompt_text:
                    chat_history[prompt_text] = chat['turns'][-1]['content'] if chat['turns'] else ""
        except Exception as e:
            console.print(f"Error loading chat history from '{chats_filepath}': {e}", style="bold red")


def _save_output_history(
    text_response, function_calls, prompt_content, system_prompt_content, local_function_calls=None
):
    global chat_history, current_chat_id
    data_path = Path(DATA_DIR)
    data_path.mkdir(exist_ok=True)
    chats_filepath = data_path / "chats.json"

    prompt_text = "".join([part.text if hasattr(part, 'text') else str(part) for part in prompt_content.parts])

    system_prompt_text = "".join([part.text if hasattr(part, 'text') else str(part) for part in system_prompt_content.parts])

    new_turn = {
        "role": "user",
        "content": prompt_text,
        "function_calls": function_calls,
        'local_function_calls': local_function_calls,  # New field for local function calls
        "timestamp": datetime.now().isoformat(),
    }

    if chats_filepath.exists():
        with open(chats_filepath, "r", encoding="utf-8") as file:
            chats_data = json.load(file)
    else:
        chats_data = []
    
    current_chat = next((chat for chat in chats_data if chat['chat_id'] == current_chat_id), None)
    if current_chat:
        current_chat['turns'].append(new_turn)
        current_chat['turns'].append({'role': 'model', 'content': text_response, 'timestamp': datetime.now().isoformat()})
    else:
        console.print(f"Error: No se encontro el chat {current_chat_id}", style="red")

    with open(chats_filepath, "w", encoding="utf-8") as file:
        json.dump(chats_data, file, indent=4)

    chat_history[prompt_text] = text_response

def _handle_function_call(response, output_format):
    full_actions_response = ""
    full_text_response = ""
    function_calls = [
        part.function_call
        for part in response.candidates[0].content.parts
        if hasattr(part, 'function_call')
    ]

    for func_call in function_calls:
        func_name = func_call.name
        args = MessageToDict(func_call.args) if func_call.args else {}
        if func_name in globals():
            try:
                function_to_call = globals()[func_name]
                result = function_to_call(**args)
                full_actions_response += f"- function_name: {func_name} - function_response: {result.uri if isinstance(result, genai.types.File) else result}\n"
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
    chat_id: str = None,
    history: list = None,
):
    global current_chat_id
    try:
        with console.status(
            "[bold yellow]Waiting for Gemini..."
        ) as status:
            if DEBUG:
                console.print("\n-- Model name:", MODEL_NAME, style="yellow")
                console.print("\n-- Prompt content parts:", style="yellow")
                for part in prompt_content.parts:
                    console.print(f"  {part}", style="yellow")

            model = _load_and_configure_model(
                system_prompt_content.parts[0].text, output_format, use_tools
            )

            if DEBUG:
                console.print("\n-- Loaded functions:", loaded_functions, style="yellow")

            chat_data = load_chat(chat_id) if chat_id else None

            if not chat_id:
                current_chat_id = create_chat(system_prompt_content.parts[0].text)
                prompt_text = "".join([part.text if hasattr(part, 'text') else str(part) for part in prompt_content.parts])
                chat_data = {
                    'chat_id': current_chat_id,
                    'system_prompt': system_prompt_content.parts[0].text,
                    'turns': [{'role': 'user', 'content': prompt_text, 'timestamp': datetime.now().isoformat()}]
                }

            if chat_data:
                current_chat_id = chat_data['chat_id']
                conversation_history = chat_data['turns']
            else:
                conversation_history = history or []

            if DEBUG:
                console.print("\n-- Conversation history:", conversation_history, style="yellow")

            conversation_history = [
                {"role": turn["role"], "parts": [{"text": turn["content"]}]}
                for turn in conversation_history
            ]

            if DEBUG:
                console.print("\n-- Conversation history (converted to Content objects):", conversation_history, style="yellow")
            
            chat = model.start_chat(history=conversation_history, enable_automatic_function_calling=use_tools) 

            full_actions_response = ""
            if use_tools and not any(hasattr(part, 'function_call') for part in prompt_content.parts):
                prompt_content = _handle_user_feedback(prompt_content)

            if use_tools:
                function_call_data = []

                for part in prompt_content.parts:
                    if hasattr(part, "function_call") and hasattr(
                        part.function_call, "name"
                    ):
                        func_call = part.function_call
                        func_name = func_call.name
                        args = getattr(func_call, "args", {})
                        if func_name in globals():
                            if DEBUG:
                                console.print(
                                    f"Calling function {func_name} with args {args}",
                                    style="blue italic",
                                )
                            try:
                                function_to_call = globals()[func_name]
                                result = function_to_call(**args)
                                if DEBUG:
                                    console.print(
                                        f"Function returned: {result}\n",
                                        style="blue italic",
                                    )
                                function_call_data.append(
                                    {
                                        "function_name": func_name,
                                        "args": args,
                                        "result": result.uri
                                        if isinstance(result, genai.types.File)
                                        else result,
                                    }
                                )
                                if isinstance(result, genai.types.File):
                                    file_data = {
                                        "mime_type": result.mime_type,
                                        "file_uri": result.uri,
                                    }
                                    prompt_content.parts.append({"file": file_data})
                                    if DEBUG:
                                        console.print(
                                            f"Prompt: {prompt_content}",
                                            style="blue italic",
                                        )
                            except Exception as e:
                                console.print(
                                    f"Error executing function {func_name}: {str(e)}",
                                    style="bold red",
                                )
                        else:
                            if func_name:
                                console.print(
                                    f"Function {func_name} is not defined",
                                    style="bold red",
                                )

                if DEBUG:
                    console.print(
                        "\n-- Prompt content before sending to Gemini:",
                        prompt_content,
                        style="yellow",
                    )

                response = chat.send_message(prompt_content)
                full_text_response = _handle_response(
                    response,
                    output_format,
                    system_prompt_content,
                    use_tools,
                    function_call_data,
                )

            chat_data['turns'].append({'role': 'user', 'content': prompt_text,  'timestamp': datetime.now().isoformat()})
            chat_data['turns'].append({'role': 'model', 'content': full_text_response, 'function_calls': function_call_data, 'timestamp': datetime.now().isoformat()})
            save_chat(chat_data)

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

            return full_text_response
    except google.api_core.exceptions.DeadlineExceeded:
        console.print(
            "Error: The request timed out. Please try again later.", style="bold red"
        )
        raise
    except google.api_core.exceptions.GoogleAPIError as e:
        console.print(f"API Error: {e.message}", style="bold red")
        raise

def _handle_option(option):
    global current_chat_id
    results_content = Content(role="assistant", parts=[])
    full_actions_response = ""
    system_prompt_content = Content(role='system', parts=[])

    while True:
        user_inputs_content = Content(role="user", parts=[])
        if "inputs" in option:
            for input_detail in option["inputs"]:
                console.print(f"{input_detail['description']}", style="yellow")
                user_input = session.prompt()
                user_inputs_content.parts.append(
                    {"text": f"[{input_detail['name']}]{user_input}[/{input_detail['name']}]"}
                )

        for action in option["actions"]:
            if DEBUG:
                console.print("Processing action:", action, style="yellow")

            result_content = _execute_action(
                action, results_content, user_inputs_content
            )

            if result_content is not None:
                if DEBUG:
                    console.print("Result content:", result_content, style="yellow")
                results_content = result_content

                has_function_calls = any(hasattr(part, 'function_call') for part in results_content.parts) if isinstance(results_content, Content) else False

                if has_function_calls:
                    if DEBUG:
                        console.print("Prompt action with function calls detected. Handling feedback.", style="yellow")

                    not_continue = option_timer(
                        "[red]Press ESC to continues[/red] - [green]Press Enter to add feedback[/green]",
                        responseOnTimeout=False,
                    )
                    if not_continue:
                        user_inputs_content = _handle_user_feedback(
                            user_inputs_content, directly=True
                        )

                if 'function_call' in action:
                    user_inputs_content.parts.append(action['function_call'])

                prompt_content = Content(role="user")
                prompt_content.parts.extend(user_inputs_content.parts)
                (system_prompt_content, _) = _format_prompt('do', None, None)

                results_content = _call_gemini_api(system_prompt_content, prompt_content, output_format=option.get('output_format', 'text'), use_tools=True, chat_id=current_chat_id)
        
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

        # Verificar si la respuesta del modelo contiene información final
        if isinstance(results_content, Content) and results_content.parts and hasattr(results_content.parts[0], 'text'):
            console.print(f"Enter another prompt:", style="yellow")
            new_input = session.prompt("> ")
            prompt_content.parts.append({"text": new_input})

            results_content = _call_gemini_api(system_prompt_content, prompt_content, output_format=option.get('output_format', 'text'), use_tools=True, chat_id=current_chat_id)
        else:
            # Si no hay información final, solicitar feedback al usuario y continuar el bucle
            not_continue = option_timer("[red]Press ESC to continues[/red] - [green]Press Enter to add feedback[/green]", responseOnTimeout=False,)
            if not_continue:
                user_inputs_content = _handle_user_feedback(user_inputs_content, directly=True)
                results_content = _handle_actions(option, results_content, user_inputs_content)


def _handle_response_chunks(model_response):
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


def _preprocess_json_response(data):
    try:
        if isinstance(data, str):
            response_json = json.loads(data)
            return response_json
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


def _handle_user_feedback(user_inputs_content, directly=False):
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
    global current_chat_id
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
            system_prompt_content, prompt_content, output_format, use_tools, chat_id=current_chat_id
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

def _handle_actions(option, previous_results_content, user_inputs_content):
    global current_chat_id
    if DEBUG:
        console.print("_handle_actions called with option:", option, style="yellow")
    if "actions" in option:
        for action in option["actions"]:
            if DEBUG:
                console.print("Processing action:", action, style="yellow")
            result_content = _execute_action(
                action, previous_results_content, user_inputs_content
            )
            if result_content is not None:
                if DEBUG:
                    console.print("Result content:", result_content, style="yellow")
                results_content = result_content
                if "prompt" in action and any(hasattr(part, 'function_call') for part in results_content.parts):
                    if DEBUG:
                        console.print("Prompt action with function calls detected. Handling feedback.", style="yellow")
                    results_content = _handle_user_feedback(results_content, directly=True)
                break
        return results_content
    else:
        console.print(
            "This option does not have any actions defined yet. Please try another option.",
            style="yellow",
        )
        display_menu()
        return None

def _handle_action(action, previous_results_content, user_inputs_content):
    global current_chat_id
    if DEBUG:
        console.print("_handle_action called with action:", action, style="yellow")
    result_content = _execute_action(
        action, previous_results_content, user_inputs_content
    )

    return result_content


def _display_other_functions(options):
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
        _exit_program()
    else:
        selected_option = options[int(choice) - 1]
        _handle_option(selected_option)
        _display_other_functions(options)

def _load_menu_options():
    with open(f"{SYSTEM_DIR}/menu_options.json", "r") as file:
        try:
            return json.load(file)
        except Exception as e:
            console.print(
                f"Error loading menu options:\n{e}", style="bold red"
            )
            _exit_program()


def save_chat(chat_data):
    global chat_history
    chats_filepath = Path(DATA_DIR) / "chats.json"

    if DEBUG:
        console.print(f"\n-- Chat data before conversion: {chat_data}", style="yellow")

    for turn in chat_data["turns"]:
        if isinstance(turn["content"], Content):
            turn['content'] = "".join([getattr(part, 'text', str(part)) for part in turn['content'].parts])

    if DEBUG:
        console.print(f"\n-- Chat data after conversion: {chat_data}", style="yellow")

    if chats_filepath.exists():
        try:
            with open(chats_filepath, "r", encoding="utf-8") as file:
                json.load(file)
        except json.JSONDecodeError:
            console.print(f"\n-- chats.json is empty or malformed. Initializing empty list.", style="yellow")
            chats_data = []
        else:
            with open(chats_filepath, "r", encoding="utf-8") as file:
                chats_data = json.load(file)
    else:
        console.print(f"\n-- chats.json does not exist. Creating an empty list.", style="yellow")
        chats_data = []

    existing_chat = next(
        (chat for chat in chats_data if chat["chat_id"] == chat_data["chat_id"]), None
    )

    if existing_chat:
        existing_chat["system_prompt"] = chat_data["system_prompt"]
        existing_chat["turns"] = chat_data["turns"]
    else:
        chats_data.append(chat_data)

    console.print(f"\n-- Chat data to be saved: {chats_data}", style="yellow")

    with open(chats_filepath, "w", encoding="utf-8") as file:
        json.dump(chats_data, file, indent=4)
                        
def load_chat(chat_id):
    chats_filepath = Path(DATA_DIR) / "chats.json"

    if not chats_filepath.parent.exists():
        chats_filepath.parent.mkdir(parents=True, exist_ok=True)

    if not chats_filepath.exists():
        with open(chats_filepath, "w", encoding="utf-8") as f:
            json.dump([], f)

    if chats_filepath.exists():
        with open(chats_filepath, "r", encoding="utf-8") as f:
            chats_data = json.load(f)
            if not chats_data:
                return None
            for chat in chats_data:
                if chat['chat_id'] == chat_id:
                    return chat
    return None


def create_chat(system_prompt):
    chat_id = str(int(time.time()))
    chat_data = {
        'chat_id': chat_id,
        'system_prompt': system_prompt,
        'turns': []
    }
    save_chat(chat_data)
    return chat_id

def list_chats():
    chats_filepath = Path(DATA_DIR) / "chats.json"
    chat_ids = []
    if chats_filepath.exists():
        with open(chats_filepath, "r", encoding="utf-8") as f:
            chats_data = json.load(f)
            sorted_chats = sorted(chats_data, key=lambda x: datetime.fromisoformat(x['turns'][-1]['timestamp']) if x['turns'] else datetime.min, reverse=True)
            chat_ids = [chat['chat_id'] for chat in sorted_chats[:20]]
    return chat_ids


def save_file_cache(file_data):
    files_filepath = Path(DATA_DIR) / "files.json"

    if files_filepath.exists():
        with open(files_filepath, "r", encoding="utf-8") as file:
            files_data = json.load(file)
    else:
        files_data = []

    existing_file = next(
        (file for file in files_data if file["file_id"] == file_data["file_id"]), None
    )
    if existing_file:
        existing_file.update(file_data)
    else:
        files_data.append(file_data)

    with open(files_filepath, "w", encoding="utf-8") as file:
        json.dump(files_data, file, indent=4)


def load_file_cache(file_id):
    files_filepath = Path(DATA_DIR) / "files.json"
    if files_filepath.exists():
        with open(files_filepath, "r", encoding="utf-8") as f:
            files_data = json.load(f)
            for file in files_data:
                if file['file_id'] == file_id:
                    return file
    return None


def list_cached_files():
    files_filepath = Path(DATA_DIR) / "files.json"
    file_ids = []
    if files_filepath.exists():
        with open(files_filepath, "r", encoding="utf-8") as f:
            files_data = json.load(f)
            # Sort by 'creation_time' in descending order and take the first 20
            sorted_files = sorted(files_data, key=lambda x: x.get('creation_time'), reverse=True)[:20]
            file_ids = [file["file_id"] for file in sorted_files]
    return file_ids


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
            except KeyError:
                console.print(f"Warning: File {file_data['file_id']} does not have an expiry time. Skipping.", style="yellow")
                updated_files_data.append(file_data)  # Include the file even without an expiry time

        # Update files.json with the updated list
        with open(files_filepath, "w", encoding="utf-8") as f:
            json.dump(updated_files_data, f, indent=4)

def display_menu():
    """Displays the main menu of the GeminiSH."""
    global current_chat_id # accesses the global chat_id
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
        _handle_option(selected_option) # Pass selected_option as argument

                        
#------------------------------------------------#
#          Main and function calls               #
#------------------------------------------------#
def continue_chat(previous_results_content, user_inputs_content):
    """Handles continuation of previous conversations."""
    global current_chat_id
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

    current_chat_id = chat_id  # sets the current_chat_id

    # Load existing chat data if chat_id is provided
    (system_prompt_content, _) = _format_prompt(
        "do", None, None # Do not add previous turns or inputs to the prompt
    )

    # Print previous conversation
    console.print("\n-- Previous conversation:", style="bold yellow")
    conversation_history = []
    for i, turn in enumerate(chat_data['turns']):
        if turn['role'] == 'user':
            # Remove [request] from the first turn
            if i == 0:
                turn['content'] = turn['content'].replace("[request]", "").replace("[/request]", "")
            console.print(f"[blue][bold]({turn['role']}):[/bold] {turn['content']}[/blue]")
            # Only add the current turn's prompt to the history
            conversation_history.append({'role': 'user', 'parts': [{'text': turn['content']}]})
        elif turn['role'] == 'model':
            console.print(f"[cyan][bold]({turn['role']}):[/bold] {turn['content']}[/cyan]")
            conversation_history.append({'role': 'model', 'parts': [{'text': turn['content']}]})
        # Add function calls to history if present
        if 'function_calls' in turn and turn['function_calls']:
            console.print(f"[magenta][bold](function calls):[/bold] {turn['function_calls']}[/magenta]")
            conversation_history.append({'role': 'function', 'parts': [{'text': turn['function_calls']}]})

    # Ask for user input
    console.print(
        Markdown(f"\n\n## Continue the conversation"), style="bold bright_blue"
    )
    user_input = session.prompt("> ")

    # Add the user input to user_inputs_content
    user_inputs_content.parts.append({"text": user_input})

    # Now create the prompt content
    (_, prompt_content) = _format_prompt('do', None, user_inputs_content)

    # Call Gemini with the full conversation history
    _call_gemini_api(
        system_prompt_content,
        prompt_content,
        chat_id=current_chat_id,
        use_tools=True,
        history=conversation_history, #  Add history argument
    )

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

    file_data = load_file_cache(file_id)
    if not file_data:
        console.print(f"Error: Could not load document {file_id}", style="red")
        return
    
    console.print(f"Viewing document {file_id}...", style="green")
    # Add logic to display the file content here
    console.print(file_data)

def upload_to_cache(document_path: str, ttl: int, display_name: str = "", description: str = "") -> str:
    """
    Uploads a document to the cache, checking if the file type is supported by Google Gemini.

    Parameters:
    document_path (str): The path to the document you want to cache.
    ttl (int): Time to live for the cached file in seconds
    display_name (str): A display name for the document (optional).
    description (str): A short description of the document (optional).

    Returns:
    str: A formatted string containing the document path and either the cached content name or an error message.
    """
    # Check if the file exists
    if not os.path.exists(document_path):
        return f"[file_path]{document_path}[/file_path][result_error]Error: File not found: {document_path}[/result_error]"

    # Get the MIME type of the file
    mime_type, _ = mimetypes.guess_type(document_path)

    # Check if the MIME type is supported
    if mime_type not in SUPPORTED_MIME_TYPES:
        return f"[file_path]{document_path}[/file_path][result_error]Error: Unsupported file type: {mime_type}. Supported types are: {SUPPORTED_MIME_TYPES}[/result_error]"

    # Upload the file to the cache
    try:
        cached_content = genai.caching.CachedContent.create(
            model=os.getenv('MODEL_NAME', 'gemini-pro'),  # Use the environment variable for the model name
            display_name=display_name if display_name else None,
            ttl=datetime.timedelta(seconds=ttl),
            description=description if description else None,
            contents=[genai.upload_file(document_path)],
        )
        console.print(
            f"Document '{document_path}' cached successfully as '{cached_content.name}'.",
            style="bold green",
        )
        return f"[file_path]{document_path}[/file_path][cached_as]{cached_content.name}[/cached_as]"
    except Exception as e:
        return f"[file_path]{document_path}[/file_path][result_error]Error caching the document: {e}[/result_error]"
    
def use_cached_document(previous_results_content, user_inputs_content):
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

    # Add the cached file to the user inputs
    user_inputs_content.parts.append({'file':{'file_uri':file_data['uri'], 'mime_type': file_data['mime_type']}})
    
    # Continue with processing the prompt
    (system_prompt_content, prompt_content) = _format_prompt('do', None, user_inputs_content)
    _call_gemini_api(system_prompt_content, prompt_content, use_tools=True, chat_id=current_chat_id)

    # Return to main menu after using the document
    display_menu()

def recreate_data_file(previous_results, user_inputs):
    """Deletes and recreates the data.txt file in the cache."""
    data_txt_path = Path(CACHE_DIR) / "data.txt"
    if data_txt_path.exists():
        data_txt_path.unlink()
        console.print("The 'data.txt' file has been recreated.", style="green")
    else:
        console.print("The 'data.txt' file did not exist.", style="yellow")
    return None

def main():
    """Main function to handle command line arguments and direct program flow."""
    try:
        if DEBUG:
            console.print("Loading chat history...", style="yellow")
            _load_chat_history()  # Loads chat history from cache on startup
        
        # Start a separate thread to check for expired files
        asyncio.run(_check_and_remove_expired_files())

        display_menu()  # Display the menu if no input is provided
    except KeyboardInterrupt:
        _exit_program()  # Call _exit_program when a keyboard interrupt is detected

        
if __name__ == "__main__":
    # Set up the signal handler for SIGINT
    signal.signal(signal.SIGINT, _handle_sigint)
    _check_api_key()
    main()
