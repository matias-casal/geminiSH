# GeminiSH Documentation

## 1. Introduction

Welcome to GeminiSH! This document provides a comprehensive guide to understanding, using, and extending GeminiSH, your personalized AI agent for enhanced productivity.

## 2. Overview

GeminiSH is a powerful Python-based command-line interface (CLI) tool that leverages Google's Gemini models to bring advanced AI capabilities directly to your terminal. It's designed to be more than just a chatbot; it's a versatile assistant that can understand natural language commands, execute complex tasks on your computer, manage files, interact with your codebase, and much more.

At its core, GeminiSH employs a dynamic, agent-based architecture. This means you can create and customize specialized AI agents for different tasks and project environments. When you run GeminiSH within a specific directory, it can adapt its functions and knowledge to that context, making it a highly flexible and personalized tool.

## 3. Core Features

*   **Interactive Chat**: Engage in natural language conversations with the powerful Google Gemini language model directly through your terminal. Get answers, generate text, brainstorm ideas, and receive assistance with various tasks.
*   **Custom Python Function Execution**: Dramatically extend GeminiSH's capabilities by defining your own Python functions. The AI can understand the docstrings of these functions and execute them to perform a wide array of customized tasks, from simple file operations to complex data analysis.
*   **Cross-Platform Compatibility**: Run GeminiSH on various operating systems, including Windows, macOS, and Linux, ensuring a consistent experience across your devices.
*   **Turn-Based Chat System**: Interact with GeminiSH in a structured, turn-by-turn manner, allowing for clear communication and easy review of the conversation flow.
*   **Rich Function Descriptions**: GeminiSH leverages detailed docstrings within your custom Python functions. This allows the AI model to deeply understand the purpose, parameters, and expected outcomes of each function, leading to more accurate and effective execution.
*   **Specialized Function Responses**: Custom functions can return standard Python data types or a special `response` object. This object allows functions to send structured data back to the agent, including `response_to_agent` messages, requests for `files_to_upload`, or indications that they `require_execution_result` from the system.
*   **System Instructions and Configuration**: Customize GeminiSH's behavior and tailor the AI's personality using `prompts/system_instructions.md`. Further configuration options are available in `config.json` to manage API keys, model parameters, and other settings.
*   **Persistent Chat History**: GeminiSH saves your conversation history in `history.json`, allowing you to resume previous sessions and maintain context over time.
*   **Command-Line Function Execution**: Execute specific, predefined custom functions directly from the command line, enabling quick, targeted actions without needing an interactive chat session.
*   **First-Time User Guidance**: New users are greeted with helpful instructions and examples from `prompts/first_runs.md` to ease the onboarding process and showcase GeminiSH's potential.
*   **Modular Manager-Based Architecture**: GeminiSH is built with a modular architecture, utilizing various managers (e.g., for functions, chat, history) to organize its codebase and allow for easier maintenance and scalability.
*   **Agent-Based Architecture**: GeminiSH supports the creation of specialized agents. By creating a `.geminiSH/` directory within a project, you can define custom functions and configurations specific to that project, making GeminiSH adapt to different contexts.
*   **File Management**: Interact with your file system through natural language. GeminiSH can be equipped with functions to create, delete, read, write, and organize files and directories.
*   **Code Interaction**: Leverage GeminiSH for software development tasks. If functions are provided, it can assist with code generation, understanding existing codebases, and applying modifications using diffs.
*   **System Automation**: Automate system-level tasks by allowing GeminiSH to execute Bash commands and run custom scripts, streamlining workflows and repetitive processes.
*   **Voice Interaction**: (If `record` function is enabled) Interact with GeminiSH using voice commands, providing a hands-free way to communicate with your AI assistant.
*   **Visual Context Awareness**: (If `screenshot` function is enabled) Allow GeminiSH to "see" your screen by capturing screenshots. This enables it to understand visual information and assist with tasks related to on-screen content.
*   **Clipboard Integration**: Seamlessly copy and paste text between GeminiSH and other applications using integrated clipboard functions.

## 4. How it Works

GeminiSH operates through a modular architecture, with different components responsible for specific tasks. This section provides insight into its internal workings.

### 4.1. Core Architecture

The application's journey begins with `main.py`. This script is responsible for initializing the `GeminiAgent`. The `GeminiAgent` acts as the central nervous system of GeminiSH. It doesn't handle tasks like user input or AI communication directly. Instead, it orchestrates a suite of specialized "manager" modules, each designed for a specific aspect of the application's functionality. This modular design keeps the codebase organized and makes it easier to update or extend specific features.

### 4.2. Manager Modules

GeminiSH's capabilities are powered by a set of dedicated manager classes:

*   **`ConfigManager`**: This manager is the custodian of configuration settings. It loads and provides access to `config.json`, which can exist both in the default GeminiSH installation directory and within a specialized agent's `.geminiSH` folder. It manages essential information like API keys for the Gemini model and provides details about the system environment (e.g., operating system).

*   **`StateManager`**: The `StateManager` keeps track of persistent application states that aren't part of the chat history. Its primary roles include managing the `system_instructions.md` file, which guides the AI's personality and behavior, and tracking whether the `first_runs.md` introductory messages have been displayed to the user.

*   **`InputManager`**: This module is responsible for capturing all user input from the command line. To enhance the user experience, it incorporates features like command history (allowing users to recall previous inputs using arrow keys) and auto-suggestions based on available commands or previous entries.

*   **`OutputManager`**: All information displayed to the user in the console passes through the `OutputManager`. It uses the `rich` library to provide formatted and visually appealing output, including standard messages, debug information, warnings, and status updates. This ensures clear and readable communication from GeminiSH to the user.

*   **`ChatManager`**: The `ChatManager` is the memory of the conversation. It maintains the `history.json` file, where all interactions (user inputs and AI responses) are stored. For the current session, it keeps track of the sequence of "turns" – each turn representing a user message or an AI response. These turns can consist of various "parts," such as plain text, function call requests from the AI, or the results of those function calls.

*   **`FunctionManager`**: This is a key component for extending GeminiSH's abilities. The `FunctionManager` discovers, loads, and manages custom Python functions located in the `functions` directory (either the default one or an agent-specific one). It reads the docstrings of these functions to generate "declarations" – structured descriptions that the Gemini model can understand. When the AI decides to use a custom function, the `FunctionManager` executes it with the parameters provided by the model. It also handles the installation of any Python dependencies required by these custom functions.

*   **`ModelManager`**: The `ModelManager` serves as the direct interface to the Google Gemini API. It handles the initialization of the AI model with the current configuration. Its main tasks are to send requests to the Gemini API (which can be chat messages from the user or responses from executed functions) and to process the output received from the model. This output can be a textual response to the user or a request to execute one of the custom functions.

### 4.3. Interaction Flow (Chat and Functions)

A typical interaction with GeminiSH, whether it's a simple chat message or a command invoking a function, follows a structured flow:

1.  **User Input**: The user types a message or command into the terminal.
2.  **Capture**: The `InputManager` captures this raw input.
3.  **Routing**: The `GeminiAgent` receives the input and determines the next step.
4.  **Direct Function Call (Optional)**: If the input is a command to directly execute a known function (e.g., a special command like `/run_function <name>`), the `FunctionManager` is invoked to execute it. The result is then typically displayed by the `OutputManager`.
5.  **Chat Message Processing**: If the input is a natural language message for the AI:
    *   The `ChatManager` adds the user's message to the current conversation history.
    *   The `ModelManager` takes the updated chat history (including any system instructions and function declarations) and sends it to the Google Gemini API.
6.  **Gemini Model Response**: The Gemini API processes the input and sends back a response. This response can be:
    *   A text message intended for the user.
    *   A request to call one of the custom functions, including the function name and the arguments it should use.
7.  **Response Processing**: The `ModelManager` receives and interprets the API's response.
8.  **Display Text**: If the response is text, the `OutputManager` displays it to the user. The conversation loop then waits for the next user input.
9.  **Function Call Execution**: If the AI requests a function call:
    *   The `FunctionManager` is tasked with executing the specified function using the arguments provided by the model.
    *   The result (output) of the function execution is captured.
    *   This function result is then added to the `ChatManager`'s history as a special "function response" turn.
    *   The `ModelManager` sends this function result back to the Gemini API, effectively telling the AI, "Here's what happened when I ran that function for you."
    *   The cycle continues: Gemini processes the function's output and typically responds with further text or another function call.

This iterative process of user input, AI processing, potential function execution, and response allows for dynamic and powerful interactions.

### 4.4. Default vs. Specialized Agents

GeminiSH introduces a powerful concept of "agents" to tailor its functionality to different contexts:

*   **Default Agent**: When you run GeminiSH, it first looks for a configuration directory named `.geminiSH/` in its own installation location (where the `gemini.sh` script or `main.py` resides). This directory houses the default set of custom functions (in `.geminiSH/functions/`), the default configuration (`.geminiSH/config.json`), system prompts (`.geminiSH/prompts/`), and chat history (`.geminiSH/history.json`). This serves as the global or fallback agent.

*   **Specialized Agents**: The real power of contextual AI comes into play when GeminiSH detects a `.geminiSH/` directory in your *current working directory* (the directory from which you launched GeminiSH). If such a directory exists, GeminiSH will prioritize using the configurations, custom functions, prompts, and history file found within this local `.geminiSH/` folder.

This agent system means you can have:
*   A **general-purpose GeminiSH** with a standard set of tools and personality when you run it from a generic location.
*   A **project-specific GeminiSH** when you run it from a particular project's root directory. This agent could have custom functions designed to interact with that project's codebase, use a different AI model configuration, or maintain a separate chat history relevant only to that project.

For example, a web development project might have an agent with functions for running a development server or deploying code, while a data science project's agent might have functions for running specific analysis scripts or visualizing data. This allows GeminiSH to be a highly adaptable and personalized tool for various workflows.

## 5. Installation and Setup

This section guides you through installing GeminiSH on your system and configuring it for first use.

### 5.1. Prerequisites

Before installing GeminiSH, ensure you have the following:

*   **Python**: Version 3.6 or higher. You can check your Python version by running:
    ```bash
    python --version
    ```
    or
    ```bash
    python3 --version
    ```
*   **PIP**: The Python package installer. PIP is usually included with Python installations. You can check its version by running:
    ```bash
    pip --version
    ```
    or
    ```bash
    pip3 --version
    ```

### 5.2. Installation

You have two main ways to install GeminiSH:

1.  **Install from PyPI (Recommended):**
    This method installs the latest stable version of GeminiSH from the Python Package Index.
    ```bash
    pip install geminish
    ```

2.  **Install from Source (for development or specific versions):**
    This method involves cloning the repository and installing it locally.
    *   Clone the Repository:
        ```bash
        git clone https://github.com/matias-casal/geminiSH.git
        ```
    *   Navigate into the directory:
        ```bash
        cd geminiSH
        ```
    *   Install the package:
        ```bash
        pip install .
        ```

### 5.3. API Key Configuration

GeminiSH requires a Google Gemini API key to interact with the AI model.

1.  **Obtain an API Key**:
    Visit the [Google AI Studio](https://aistudio.google.com/app/apikey) to create and obtain your API key.

2.  **Set the API Key**:
    You need to make your API key available to GeminiSH. There are two ways to do this:

    *   **Method 1: Configuration File (`config.json`)**
        When you run GeminiSH for the first time (or if you've installed from source and the `.geminiSH` directory is present), it will look for a `config.json` file.
        *   **Default Location**: If you installed via `pip install geminish`, a default `.geminiSH` directory (containing `config.json`, `history.json`, etc.) is typically created in your user's home directory (e.g., `~/.geminiSH/` on Linux/macOS, or `%USERPROFILE%\.geminiSH\` on Windows) upon first run if it doesn't exist.
        *   **Project-Specific Agent**: If you run `geminiSH` within a directory that has its own `.geminiSH/` subfolder, it will use the `config.json` from there.
        *   **Cloned Repository**: If you cloned the repository, there's a `.geminiSH` directory at the root of the project. You can edit the `config.json` file within it.

        Open or create the `config.json` file in the relevant `.geminiSH` directory and add/update the `GOOGLE_API_KEY` field:
        ```json
        {
          "GOOGLE_API_KEY": "YOUR_API_KEY_HERE",
          "GEMINI_MODEL": "gemini-1.5-pro-latest",
          "MAX_OUTPUT_TOKENS": 2048,
          "TEMPERATURE": 0.7,
          "MAX_HISTORY_TURNS": 10
        }
        ```
        *(Ensure the rest of the JSON structure remains valid if you are editing an existing file.)*

    *   **Method 2: Environment Variable**
        You can set the `GOOGLE_API_KEY` as an environment variable. GeminiSH will prioritize this method if the variable is set.
        ```bash
        export GOOGLE_API_KEY="YOUR_API_KEY_HERE"
        ```
        To make this setting permanent, add this line to your shell's configuration file (e.g., `~/.bashrc`, `~/.zshrc` for Linux/macOS, or manage environment variables through System Properties on Windows).

### 5.4. Initial Run

Once installed and configured with your API key, you can start GeminiSH by simply typing the following command in your terminal:

```bash
geminiSH
```

On the first run in a new environment (or if the default configuration is missing), GeminiSH may initialize its default `.geminiSH` directory. If you are working within a project and want to create a specialized agent, you can create a `.geminiSH` folder in your project's root directory. GeminiSH will then use that folder for its configuration, functions, and history for that specific project context. You'll be greeted with a welcome message and some examples to get you started.

## 6. Usage

This section explains how to use GeminiSH, from basic chat to advanced function creation.

### 6.1. Starting GeminiSH

To start GeminiSH in its default interactive chat mode, simply open your terminal and type:

```bash
geminiSH
```
This will launch the AI agent, and you can begin interacting with it.

### 6.2. Interactive Chat

Once GeminiSH is running, you can communicate with the AI using natural language.

*   **Conversing**: Type your questions, commands, or prompts and press Enter. The AI will process your input and respond.
*   **Multi-turn Conversations**: GeminiSH remembers the context of the current conversation (up to a configurable limit defined in `config.json` or by default values). This allows you to have back-and-forth dialogues, ask follow-up questions, and refine requests.
*   **Exiting**: To exit GeminiSH, you can typically use `Ctrl+C`. You can also type `exit` or `quit` as a command.

### 6.3. Direct Function Execution

GeminiSH allows you to execute specific custom functions directly from the command line without starting an interactive chat session. This is useful for quick tasks or scripting.

*   **Syntax**:
    ```bash
    geminiSH function_name [argument_string]
    ```
    *   `function_name`: The exact name of the Python function you want to execute (as defined in one of your custom function files).
    *   `[argument_string]`: (Optional) A single string containing all the arguments for the function. If your function takes multiple arguments, they should be included in this single string, separated by spaces or formatted as the function expects to parse them.

*   **Examples**:
    *   To execute a function named `record` (which might be a built-in or custom function for voice input):
        ```bash
        geminiSH record
        ```
    *   To execute a custom function `my_custom_function` that takes a string argument:
        ```bash
        geminiSH my_custom_function 'some important arguments here'
        ```
    *   To execute a function `search_files` that takes a pattern and a directory:
        ```bash
        geminiSH search_files 'pattern="*.txt" directory="/home/user/docs"'
        ```
        (Note: The function `search_files` would need to be designed to parse this specific argument string format.)

*   **Argument Handling**: When you provide an `argument_string`, GeminiSH passes it as a single string to the target function. The function itself is responsible for parsing this string if multiple arguments are needed. For functions designed to be called by the AI, the AI uses the structured parameter schema (derived from docstrings and type hints), but for direct CLI execution, this single string input is the mechanism.

### 6.4. Creating Custom Functions

The true power of GeminiSH comes from its ability to execute custom Python functions. This allows you to tailor the AI's capabilities to your specific needs and workflows.

#### 6.4.1. Function Location

Custom functions are Python (`.py`) files placed in a specific directory:

*   **Default Agent**: For the default GeminiSH agent, place your function files in the `.geminiSH/functions/` directory. The location of this main `.geminiSH` directory depends on your installation:
    *   If installed via `pip install geminish`, it's typically in your user's home directory (e.g., `~/.geminiSH/functions/` on Linux/macOS, `%USERPROFILE%\.geminiSH\functions\` on Windows).
    *   If you cloned the repository and are running from there, it's `your_clone_directory/.geminiSH/functions/`.
*   **Specialized Agent**: If you have created a specialized agent by making a `.geminiSH/` folder within a specific project directory, place your function files in `your_project_directory/.geminiSH/functions/`. These functions will only be available when running `geminiSH` from that project directory.

Each `.py` file can contain one or more functions.

#### 6.4.2. Function Definition

Functions are defined using standard Python syntax.

```python
# Example: in .geminiSH/functions/string_tools.py

def reverse_string(text: str) -> str:
    # ... implementation ...
    return text[::-1]

def count_words(text: str) -> int:
    # ... implementation ...
    return len(text.split())
```

#### 6.4.3. Docstrings: Guiding the AI

Docstrings are **critical** for custom functions. The Gemini model uses the docstring to understand what the function does, what its parameters are, and, most importantly, *when it should be called*. A well-written docstring acts as the primary instruction manual for the AI.

**Docstring Content:**

*   **Purpose**: Clearly describe what the function accomplishes.
*   **When to Use**: Provide context or example scenarios for when the AI should consider using this function. This is very important for the AI to make good decisions.
*   **Arguments (`Args`)**:
    *   List each parameter.
    *   Specify its type (e.g., `str`, `int`, `list`).
    *   Describe what the parameter represents.
*   **Returns (`Returns`)**:
    *   Describe the expected output of the function. If it's a dictionary with specific keys for agent interaction, detail those.

**Example of a good docstring:**

```python
def search_knowledge_base(query: str, category: str = "general") -> str:
    """
    Searches the company's knowledge base for articles matching the user's query.
    Use this function when the user asks a question that can likely be answered by an internal help article or document.
    For example, if the user asks "How do I reset my VPN password?", this function can be used.

    Args:
        query (str): The user's search query or question.
        category (str, optional): The category to search within (e.g., "technical", "hr", "product").
                                  Defaults to "general" if not specified.

    Returns:
        str: A summary of the top search result or a message if no relevant articles are found.
    """
    # ... function implementation ...
    pass
```

#### 6.4.4. Type Hinting for Parameters

Python type hints in your function parameters are used by the `FunctionManager` to generate a structured schema for the AI. This schema tells the AI the names of the parameters and their expected data types (e.g., string, number, boolean, array). The AI then uses this schema to format its requests to call your function.

```python
def schedule_meeting(title: str, participants: list[str], start_time: str, duration_minutes: int = 30):
    """
    Schedules a new meeting in the calendar.

    Args:
        title (str): The title or subject of the meeting.
        participants (list[str]): A list of email addresses of the participants.
        start_time (str): The start time of the meeting in ISO 8601 format (e.g., "2024-07-15T14:00:00").
        duration_minutes (int, optional): The duration of the meeting in minutes. Defaults to 30.
    """
    # ... implementation ...
    pass
```
In this example, the AI will know to provide a string for `title`, a list of strings for `participants`, a string for `start_time`, and an integer for `duration_minutes`.

#### 6.4.5. Return Values and Agent Responses

Functions can return information in several ways:

1.  **Simple String Response**:
    If a function returns a simple string, this string is sent back to the model as the result of the function call. The model will then use this information in its response to the user.

    ```python
    def get_current_time() -> str:
        """Returns the current date and time."""
        import datetime
        return f"The current time is: {datetime.datetime.now()}"
    ```

2.  **Dictionary for Complex Responses**:
    For more complex interactions or to trigger agent-specific actions, a function can return a dictionary. This dictionary can have the following keys:

    *   `"response"` (str, optional): A string summary, result, or message that will be sent to the model. This is similar to the simple string response and can be used by the model in its reply to the user.
    *   `"response_to_agent"` (dict, optional): A dictionary containing instructions for the GeminiSH agent itself. This allows functions to trigger actions beyond just sending text back to the model.
        *   `"files_to_upload": ["/path/to/file1", "/path/to/file2.txt"]`:
            This instructs GeminiSH to automatically call the `upload_files` function (or a similar internal mechanism) for each file path provided in the list. This is useful if your function generates or identifies files that the AI should be made aware of for future context or operations. The model will be informed that these files have been "uploaded" (i.e., made available to it).
        *   `"require_execution_result": True`:
            If `True`, this indicates that the result of this function (the content of the `"response"` field, or a default message if no response field is provided) should be immediately sent back to the model for its next turn, without waiting for further user input. This is useful for functions that perform a quick, essential step that the AI needs to continue its reasoning. (Note: The exact behavior of this flag can depend on the GeminiSH version and configuration).
        *   `"load_chat_history": "chat_session_id_or_filename"`:
            This instructs GeminiSH to load a specific chat history. This could be used to switch contexts or resume a previous conversation. The string value should be an identifier that the `ChatManager` can use to locate and load the desired history.

**Examples of Dictionary Responses:**

*   **Returning a simple message via the dictionary:**
    ```python
    def set_user_preference(theme: str) -> dict:
        """Sets a user preference, like theme."""
        # ... logic to save theme ...
        return {"response": f"User theme preference set to {theme}."}
    ```

*   **Function generating a file and informing the agent:**
    ```python
    def generate_report(data: list, output_filename: str = "report.txt") -> dict:
        """Generates a report from data and saves it to a file."""
        import os
        filepath = os.path.join(os.getcwd(), output_filename)
        with open(filepath, "w") as f:
            f.write("Report Data:\n")
            for item in data:
                f.write(f"- {item}\n")
        return {
            "response": f"Report generated and saved to {output_filename}.",
            "response_to_agent": {
                "files_to_upload": [filepath]
            }
        }
    ```

#### 6.4.6. Dependency Management

If your custom Python functions import libraries that are not part of the standard Python library or already installed in GeminiSH's environment, the `FunctionManager` will attempt to automatically install these missing dependencies using `pip` when it first loads the functions. For this to work reliably:

*   Ensure the module names in your `import` statements match the package names on PyPI (e.g., `import requests` requires the `requests` package).
*   It's good practice to manage complex dependencies for specialized agents within a virtual environment that you activate before running GeminiSH.

#### 6.4.7. Example Custom Functions

Here are a couple of illustrative examples:

```python
# In .geminiSH/functions/file_operations.py

def get_file_size(filepath: str) -> str:
    """
    Calculates the size of a specified file and returns it in a human-readable format.
    Use this function when the user asks for the size of a particular file.

    Args:
        filepath (str): The full path to the file.
    """
    import os
    try:
        size_bytes = os.path.getsize(filepath)
        if size_bytes == 0:
            return "0 bytes"
        elif size_bytes < 1024:
            return f"{size_bytes} bytes"
        elif size_bytes < 1024**2:
            return f"{size_bytes/1024:.2f} KB"
        elif size_bytes < 1024**3:
            return f"{size_bytes/(1024**2):.2f} MB"
        else:
            return f"{size_bytes/(1024**3):.2f} GB"
    except FileNotFoundError:
        return f"Error: File not found at {filepath}"
    except Exception as e:
        return f"Error calculating file size: {e}"

def create_backup(source_file: str, backup_location: str) -> dict:
    """
    Creates a backup of a given file to a specified directory.
    The backup file will be named 'backup_' followed by the original filename.

    Args:
        source_file (str): The path to the file to be backed up.
        backup_location (str): The directory where the backup file should be saved.
    
    Returns:
        dict: A dictionary containing a response message.
              Includes 'files_to_upload' with the path to the new backup file.
    """
    import shutil
    import os
    if not os.path.isfile(source_file):
        return {"response": f"Error: Source file '{source_file}' not found."}
    if not os.path.isdir(backup_location):
        return {"response": f"Error: Backup location '{backup_location}' is not a valid directory."}
    
    try:
        base_filename = os.path.basename(source_file)
        backup_filename = f"backup_{base_filename}"
        backed_up_file_path = os.path.join(backup_location, backup_filename)
        
        shutil.copy2(source_file, backed_up_file_path) # copy2 preserves metadata
        
        return {
            "response": f"Successfully backed up '{source_file}' to '{backed_up_file_path}'.",
            "response_to_agent": {
                "files_to_upload": [backed_up_file_path]
            }
        }
    except Exception as e:
        return {"response": f"Error creating backup for '{source_file}': {e}"}

```

### 6.5. Specialized Agents

As mentioned in the "How it Works" section (4.4), GeminiSH's agent system allows you to create highly customized instances for different projects or tasks.

*   **Activation**: To use a specialized agent, simply navigate to your project directory (which contains its own `.geminiSH/` subfolder) in your terminal and run the `geminiSH` command from there.
*   **Contextualization**: This local `.geminiSH/` directory will house its own:
    *   `config.json`: For agent-specific settings (e.g., a different Gemini model, temperature, or custom API keys if needed).
    *   `functions/`: A dedicated set of Python functions relevant only to this agent's purpose.
    *   `prompts/system_instructions.md`: Tailored system instructions to guide the AI's behavior and expertise for this context.
    *   `history.json`: A separate chat history, keeping conversations for this agent isolated.

*   **Use Case Example**:
    Imagine you're working on a Python web application in a directory named `my_web_app/`. You could create `my_web_app/.geminiSH/` and populate it:
    *   `my_web_app/.geminiSH/functions/dev_tools.py`: Containing functions like `run_tests()`, `start_dev_server()`, `lint_code(filepath: str)`, or `git_commit(message: str)`.
    *   `my_web_app/.geminiSH/prompts/system_instructions.md`: "You are an expert Python web development assistant. Help with Flask, Django, testing, and git operations. Be concise and provide code examples."
    *   `my_web_app/.geminiSH/config.json`: Perhaps configured to use a model better suited for code generation.

When you run `geminiSH` from within `my_web_app/`, it will automatically become this specialized web development assistant, equipped with the relevant tools and knowledge. Running `geminiSH` from any other directory would use the default agent or another specialized agent if present.

## 7. Configuration

GeminiSH's behavior can be customized through a configuration file and environment variables.

### 7.1. `config.json` File

Each GeminiSH agent (whether the default one created in your home directory or a specialized one in a project's `.geminiSH/` subfolder) uses a `config.json` file. This file is located within the agent's directory (e.g., `~/.geminiSH/config.json` or `your_project/.geminiSH/config.json`).

Here are the key configuration options available:

*   **`GOOGLE_API_KEY`**: Your Google Gemini API key. This is essential for connecting to the AI model. (As covered in Installation).
    ```json
    "GOOGLE_API_KEY": "YOUR_API_KEY_HERE"
    ```
*   **`DEBUG`**: A boolean (`true` or `false`) that enables or disables verbose debug logging. Useful for troubleshooting.
    ```json
    "DEBUG": false
    ```
*   **`AGENT_DIR`**: The name of the directory where agent-specific files (functions, prompts, history) are stored. Defaults to `.geminiSH`.
    ```json
    "AGENT_DIR": ".geminiSH"
    ```
*   **`REMOVE_CACHE_AFTER_LOAD`**: A boolean. If set to `true`, it's likely intended to clear any cached data related to function definitions or other resources after they are loaded, potentially to save memory or ensure fresh loading on next run.
    ```json
    "REMOVE_CACHE_AFTER_LOAD": false
    ```
*   **`SAVE_PROMPT_HISTORY`**: A boolean. If `true`, the prompts (user inputs) sent to the model are saved in the chat history (`history.json`).
    ```json
    "SAVE_PROMPT_HISTORY": true
    ```
*   **`SAVE_OUTPUT_HISTORY`**: A boolean. If `true`, the outputs (model responses) received from the model are saved in the chat history.
    ```json
    "SAVE_OUTPUT_HISTORY": true
    ```
*   **`WARNING_TOKENS_THRESHOLD`**: A floating-point number (e.g., 0.9) representing a percentage. When the number of tokens used in a conversation approaches the model's maximum token limit (defined by `MODEL_MAX_TOKENS`) and exceeds this threshold, a warning may be displayed.
    ```json
    "WARNING_TOKENS_THRESHOLD": 0.9
    ```
*   **`MODEL_NAME`**: Specifies the particular Google Gemini model to be used for the chat.
    ```json
    "MODEL_NAME": "gemini-1.5-pro-latest"
    ```
*   **`MODEL_MAX_TOKENS`**: The maximum number of tokens (pieces of words) that the model can consider in a single context (prompt + response). This also limits the length of the response.
    ```json
    "MODEL_MAX_TOKENS": 2097152
    ```
*   **`MODEL_SAFETY_SETTINGS`**: An object to configure the content safety filters applied by the Gemini model. For each category (`HATE`, `HARASSMENT`, `SEXUAL`, `DANGEROUS`), you can specify a blocking threshold (e.g., `BLOCK_NONE`, `BLOCK_LOW_AND_ABOVE`, `BLOCK_MEDIUM_AND_ABOVE`, `BLOCK_HIGH_AND_ABOVE`).
    ```json
    "MODEL_SAFETY_SETTINGS": {
      "HATE": "BLOCK_NONE",
      "HARASSMENT": "BLOCK_NONE",
      "SEXUAL": "BLOCK_NONE",
      "DANGEROUS": "BLOCK_NONE"
    }
    ```
*   **`MODEL_SUPPORTED_MIME_TYPES`**: A list of strings, where each string is a MIME type (e.g., "image/png", "text/plain", "application/pdf") that the model supports for file uploads. This informs GeminiSH what kinds of files can be processed by the AI.
    ```json
    "MODEL_SUPPORTED_MIME_TYPES": [
      "image/png", "image/jpeg", /* ... shortened for brevity ... */ "application/pdf"
    ]
    ```

**Caution:** Be careful when manually editing the `config.json` file. Incorrect formatting or invalid values can cause GeminiSH to behave unexpectedly or fail to start. It's often safer to modify settings through GeminiSH itself if such functions are available, or to ensure you have a backup of the file.

### 7.2. Environment Variables

Some GeminiSH settings can be influenced or overridden by environment variables. This is particularly useful for temporary adjustments or in environments where direct file editing is not ideal.

*   **`GOOGLE_API_KEY`**:
    As mentioned in the setup, you can set your API key using an environment variable. If set, this will typically take precedence over the key in `config.json`.
    ```bash
    export GOOGLE_API_KEY="YOUR_API_KEY_HERE"
    ```

*   **`DEBUG`**:
    You can enable debug mode by setting the `DEBUG` environment variable to `True`. This often provides more verbose output for troubleshooting. The `OutputManager` checks `os.getenv("DEBUG", "False") == "True"`. If both the `config.json` and this environment variable are set, the environment variable might take precedence, or they might both contribute to enabling debug mode.
    ```bash
    export DEBUG=True
    # To run for a single session:
    # DEBUG=True geminiSH
    ```

*   **`FIRST_RUN_THRESHOLD`**:
    The `ChatManager` (specifically `ChatManager.get_recent_history`) uses an environment variable `FIRST_RUN_THRESHOLD` which defaults to 3. This likely influences how many past chat sessions are considered "recent" or loaded during certain initial run behaviors or when displaying initial guidance.
    ```bash
    export FIRST_RUN_THRESHOLD=5 
    ```

It's possible that other components within GeminiSH or its custom functions might also respond to other environment variables. Always refer to specific module documentation or code if you suspect an environment variable is influencing behavior. Precedence between `config.json` settings and environment variables is usually that environment variables override `config.json` values if both are set for the same parameter, but this can depend on the specific implementation within GeminiSH.

## 8. Understanding the GeminiSH Directory Structure

GeminiSH relies on a special directory, typically named `.geminiSH`, to store its configuration, custom functions, prompts, and history. Understanding this structure helps in customizing and managing your agents.

### 8.1. The `.geminiSH` Agent Directory

The `.geminiSH` directory serves as the central workspace for an agent, whether it's the default global agent or a specialized one.

*   **Default Agent Directory**:
    When you install and run GeminiSH for the first time (e.g., via `pip install geminish` and then running the `geminiSH` command), or if you run it directly from the cloned repository source, a default `.geminiSH` directory is established.
    *   **Location**:
        *   If installed as a package, this directory is typically created in your user's home directory (e.g., `~/.geminiSH/` on Linux/macOS, or `%USERPROFILE%\.geminiSH\` on Windows). This ensures each user has their own default agent settings.
        *   If running from the cloned repository, the primary `.geminiSH` directory is located at the root of the cloned project. This version is often used for development or as a template.
    *   **Purpose**: This directory houses the global/default functions, prompts, and configuration that GeminiSH will use if no specialized agent is detected in the current working directory.

*   **Specialized Agent Directory (Current Working Directory - CWD)**:
    The true power of GeminiSH's agent system comes to life when you create a `.geminiSH` directory *within one of your own project folders* (e.g., `/path/to/my_project/.geminiSH/`).
    *   **Activation**: When you run the `geminiSH` command from inside `/path/to/my_project/`, it will detect the local `.geminiSH/` directory.
    *   **Override and Customization**: This local directory becomes the active agent's workspace. It allows you to have specialized configurations (`config.json`), custom Python functions (`functions/`), unique system prompts (`prompts/`), and a dedicated chat history (`history.json`) tailored specifically to that project or context.
    *   **Precedence**: Settings, functions, and prompts found in the CWD's `.geminiSH` directory will take precedence and override those in the default/global agent directory. This ensures that the agent adapts to the specific needs of the project you are working on.

### 8.2. Inside `.geminiSH`

Here's a breakdown of the important files and subdirectories you'll find within any `.geminiSH` directory (default or specialized):

*   **`functions/`**:
    *   **Purpose**: This directory is where you place your custom Python scripts (`.py` files). Each script can contain one or more functions designed to extend GeminiSH's capabilities.
    *   **Loading**: The `FunctionManager` is responsible for discovering and loading these functions. It makes them available to the AI model, which can then request their execution based on your interactions. If a specialized agent has a `functions/` directory, those functions are prioritized and loaded for that agent.

*   **`prompts/`**:
    *   **Purpose**: This directory holds Markdown (`.md`) files that define how the AI agent behaves, its personality, and initial interactions.
    *   **`system_instructions.md`**: This is a critical file. It contains the core instructions, rules, persona guidelines, and constraints for the Gemini model. The `StateManager` loads these instructions, and the `ModelManager` uses them to set the AI's behavior for every conversation. You can (and should) edit this file in a specialized agent's `.geminiSH/prompts/` directory to tailor the agent's expertise, responses, and operational scope.
    *   **`first_runs.md`**: Contains the introductory message and examples shown to users the first few times they run GeminiSH in a new context (i.e., when a new `history.json` is created or is very short). This is managed by the `StateManager` and displayed via the `ModelManager` to help with onboarding. This can also be customized for specialized agents.

*   **`config.json`**:
    *   **Purpose**: The primary JSON configuration file for the agent.
    *   **Content**: It stores crucial settings such as the `GOOGLE_API_KEY`, the specific `MODEL_NAME` to use (e.g., `gemini-1.5-pro-latest`), `MODEL_MAX_TOKENS`, safety settings for content filtering, and other operational parameters. The `ConfigManager` loads this file. (Refer to the "7. Configuration" section for a detailed list of options).

*   **`history.json`**:
    *   **Purpose**: All chat conversations are saved in this file by the `ChatManager`. This allows for persistent memory across sessions.
    *   **Format**: It's a JSON file where each conversation (or session) is stored, typically including a sequence of "turns." Each turn represents a part of the dialogue, such as a user's message, the AI model's textual response, a function call requested by the model, or the result returned by an executed function. This structured history is crucial for maintaining context in ongoing interactions.

## 9. Contributing to GeminiSH

GeminiSH is an open-source project, and contributions from the community are highly welcome! Whether you're fixing a bug, adding a new function, improving documentation, or sharing your use cases, your help is appreciated. Your involvement helps make GeminiSH better for everyone.

Here are some ways you can contribute:

### 9.1. Reporting Bugs and Issues

If you encounter unexpected behavior, a bug, or have any other issue:

*   **Check Existing Issues**: Before submitting a new issue, please take a moment to check the [GitHub Issues page](https://github.com/matias-casal/geminiSH/issues) to see if someone else has already reported it. If so, you can often add more information to the existing report.
*   **Open a New Issue**: If your issue is new, please create a new issue. Provide as much detail as possible to help us understand and reproduce the problem. Key information includes:
    *   Clear and concise steps to reproduce the issue.
    *   What you expected to happen and what actually happened.
    *   Your operating system (e.g., Windows 10, macOS Sonoma, Ubuntu 22.04).
    *   Your Python version (e.g., `python --version`).
    *   Any error messages displayed, along with relevant parts of the console output (especially if DEBUG mode was enabled).
    *   Screenshots or GIFs can also be very helpful for visual issues.

### 9.2. Suggesting Enhancements

Have an idea for a new feature, a change to an existing one, or a general improvement?

*   **Create an Enhancement Request**: Open a new issue on GitHub. Select the "Feature request" template if available, or clearly indicate that it's an enhancement suggestion.
*   **Describe Your Idea**: Provide a clear and detailed explanation of the proposed enhancement.
    *   What is the new feature or improvement?
    *   Why do you think it would be beneficial to GeminiSH and its users?
    *   If possible, provide examples of how it might work or be used.

### 9.3. Adding New Functions

This is one of the most direct and impactful ways to contribute to GeminiSH's capabilities.

*   **Develop Your Function**: Create your Python function(s) in a `.py` file.
*   **Write Excellent Docstrings**: This is crucial. The AI model relies heavily on docstrings to understand the function's purpose, its parameters (arguments), what it returns, and, most importantly, *in what situations it should be used*. Include type hints for all parameters. (See section "6.4.3. Docstrings: Guiding the AI" and "6.4.4. Type Hinting for Parameters" for details).
*   **Consider Generality**: If you create a function that you believe could be broadly useful to other GeminiSH users (i.e., not specific to a niche personal workflow), please consider sharing it!
*   **Share via Pull Request**: You can contribute new generic functions to the core set of default functions by submitting them via a Pull Request. Place your function file in the `geminish/.geminiSH/functions/` directory in your fork before creating the PR.

### 9.4. Improving Documentation

Clear, accurate, and comprehensive documentation is vital for any project.

*   **Updates and Fixes**: If you notice typos, errors, outdated information, or areas that could be explained better in this `DOCUMENTATION.md` file, the `README.md`, or any other documentation (like docstrings in the core code), please consider contributing.
*   **Submit Changes**: You can suggest changes by opening an issue or, for more direct contributions, by submitting a Pull Request with your proposed improvements.

### 9.5. Code Contributions (Pull Requests)

For direct code contributions, such as bug fixes, implementing approved enhancements, or adding new core features:

1.  **Fork the Repository**: Create your own copy of the [GeminiSH repository](https://github.com/matias-casal/geminiSH) on GitHub.
2.  **Create a Branch**: In your fork, create a new branch for your changes. Use a descriptive name, for example:
    *   `feature/your-cool-new-feature`
    *   `fix/bug-in-function-manager`
    *   `docs/update-contributing-guide`
3.  **Make Your Changes**: Implement your code, fix, or documentation update.
4.  **Commit Your Changes**: Write clear, concise commit messages that explain the purpose of your changes.
5.  **Follow Code Style**: Try to follow the existing code style and conventions used in the GeminiSH codebase to maintain consistency. (While a formal style guide might not be explicitly stated, observe patterns in existing code regarding naming, formatting, etc.)
6.  **Add Tests (If Applicable)**: If you're adding a new feature or fixing a bug that can be covered by unit tests, please consider adding them. (The project may or may not have an extensive test suite, but contributions towards testability are always welcome).
7.  **Push to Your Fork**: Push your changes to the branch in your forked repository.
8.  **Open a Pull Request**: Go to the original GeminiSH repository and open a Pull Request from your branch to the main development branch of GeminiSH. Provide a clear description of your changes in the Pull Request.

### 9.6. Sharing Ideas and Use Cases

We are always excited to learn about the creative and practical ways users are leveraging GeminiSH.

*   **Share Your Workflows**: If you've built a specialized agent for a particular task or integrated GeminiSH into your workflow in an interesting way, consider sharing your setup (e.g., custom functions, system prompts).
*   **Discuss Possibilities**: Join discussions on the GitHub repository (if available) or other community channels to share ideas, ask questions, and inspire others. Your real-world use cases can help guide the future development of GeminiSH.
