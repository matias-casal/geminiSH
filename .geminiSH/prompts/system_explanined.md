## Gemini SH: A Deep Dive into its Architecture and Capabilities

Gemini SH is a sophisticated Python-based AI agent powered by Google Gemini, designed to facilitate dynamic and versatile interactions between the user and their computer. This document provides a comprehensive overview of its architecture, core features, and potential use cases.

**Core Architecture:**

Gemini SH operates on a modular architecture, leveraging several key managers to handle specific aspects of the system:

- **`ConfigManager`:** Manages the configuration settings loaded from `config.json`, including API keys, model parameters, and safety settings. It also handles the identification and loading of agent-specific configurations.

- **`StateManager`:** Tracks the state of the application, such as whether it's the first run and the system instructions provided to the Gemini model.

- **`InputManager`:** Handles user input through the terminal, providing features like auto-completion and a history of previous commands.

- **`OutputManager`:** Manages the output to the terminal, supporting rich text formatting and markdown rendering. It also provides tools for debugging and displaying status messages.

- **`ChatManager`:** Maintains the history of the conversation with the Gemini model, storing both user inputs and model responses in a structured format. It also handles loading and saving chat sessions.

- **`FunctionManager`:** Loads and manages the available functions that extend the capabilities of the agent. It converts Python functions into declarations that the Gemini model can understand and execute. It also handles the execution of these functions and the processing of their responses.

- **`ModelManager`:** Initializes and interacts with the Google Gemini model. It sends user inputs and function calls to the model, receives responses, and handles the execution of any requested functions.

**Dynamic Agent-Based Approach:**

Gemini SH employs a dynamic agent-based approach, enabling the creation of specialized agents tailored to specific tasks and environments. When the `geminiSH` command is executed within a directory, a `.geminiSH` folder is created, serving as the agent's workspace. This folder houses its configuration, history, and custom functions, allowing for a high degree of customization and specialization.

**Core Features and Capabilities:**

- **Interactive Chat:** Enables natural language conversations with the Gemini model through the terminal.

- **Function Execution:** Extends the capabilities of the agent beyond simple chat interactions by allowing the execution of user-defined Python functions.

- **Cross-Platform Compatibility:** Designed to run seamlessly on any terminal and operating system.

- **Turn-Based Chat System:** Structures conversations in turns, ensuring clear communication and back-and-forth interactions.

- **Customizable Functions:** Allows users to expand the agent's capabilities by adding Python scripts with custom functions to the `functions` directory.

- **Rich Function Descriptions:** Leverages docstrings to provide detailed information about each function, including its purpose, parameters, return values, and usage scenarios.

- **Specialized Function Responses:** Functions can return different types of responses, including:

  - **Standard String Responses:** Directly returned to the model as text.
  - **`response` Object:** Contains a `response` field for the model and a `response_to_agent` field for triggering specific actions within Gemini SH.
  - **Actionable Responses:** The `response_to_agent` field can include instructions like:
    - `files_to_upload`: A list of file paths to be uploaded to Google Gemini.
    - `load_chat_history`: The ID of a chat session to be loaded.
    - `require_execution_result`: A boolean indicating whether the function's result should be immediately sent back to the model.

- **System Instructions and Configuration:**

  - `prompts/system_instructions.md`: Contains the initial instructions for the Gemini model, defining its role and behavior.
  - `config.json`: Allows configuration of various system settings, including the Gemini model to use and saving options.

- **Persistent Chat History:** Saves conversations in `history.json` for future reference and analysis.

- **Command-Line Function Execution:** Enables the execution of functions directly from the command line by passing the function name and arguments.

- **First-Time User Guidance:** Provides a helpful message explaining the system's functionalities and usage during initial runs.

**Use Cases:**

Gemini SH offers a wide range of potential applications, including:

- **File Management:** Organizing and processing files based on user requests.
- **Code Interaction:** Assisting with coding errors, generating code snippets, and modifying source files directly through diffs.
- **System Automation:** Automating repetitive tasks and workflows through custom functions and bash commands.
- **Content Creation:** Generating presentations and other content based on text input.
- **Information Retrieval:** Answering questions based on the content of local files and documentation.
- **Voice Interaction:** Recording audio and sending it to Gemini for hands-free communication.
- **Visual Context Awareness:** Taking screenshots to provide Gemini with visual context for more relevant responses.
- **Cross-Application Integration:** Using the clipboard to exchange data with other applications.

**Extensibility and Customization:**

The core strength of Gemini SH lies in its extensibility and customization capabilities. Users can create new functions to expand the agent's skillset and tailor its behavior to specific needs. The dynamic agent-based architecture further enhances this flexibility, allowing for the creation of specialized agents optimized for different tasks and environments.

````
## Function Construction and Dynamic Loading in Gemini SH: A Detailed Analysis

Functions in Gemini SH are defined in Python files within the `.geminiSH/functions` folder. Each file can contain one or more functions, and the way these functions are constructed is crucial for their correct integration with the system.

**Structure of a Function:**

1. **Documentation (Docstring):** Each function must begin with a docstring that describes its purpose, parameters, return value, and when it should be used. This docstring is fundamental for the Gemini language model to understand the function and use it appropriately.

2. **Function Code:** The function code should be clear, concise, and well-documented with comments. It's important to follow programming best practices to ensure code readability and maintainability.

3. **Function Return:** The function's return type determines how the system will process the response:

   - **`str` (text string):** The string is sent directly to the language model as part of the response. This is the simplest return type and is used for informative responses or error messages.

   - **`dict` (dictionary):** The dictionary can contain two keys: `response` and `response_to_agent`.
     - `response`: A text string that is sent to the language model as part of the response.
     - `response_to_agent`: A dictionary with instructions for the agent. These instructions can include:
       - `files_to_upload`: A list of file paths that will be uploaded to Google Gemini.
       - `load_chat_history`: The ID of a chat that will be loaded from the history.
       - `require_execution_result`: A boolean value that indicates whether the function's result should be sent immediately to the model (True) or if it should wait for the next user interaction (False).

**Example of a Function:**

```python
def get_content_file(file_path):
    """
    Processes a file and obtains its content.
    If the user wants to work with a file, this function is executed first.

    Args:
        file_path (str): File path.

    Returns:
        dict: A dictionary with the response for the user and an instruction for the agent.
    """
    # ... function code ...

    return {
        "response": "The file has been processed successfully.",
        "response_to_agent": {"files_to_upload": [file_path], 'require_execution_result': True}
    }
````

**Dynamic Function Loading:**

The system loads functions dynamically from the `.geminiSH/functions` folder. This means that it is not necessary to restart the system for new functions to be available. However, it is important to keep in mind that:

## Expanding Gemini SH: Custom Handling of Function Responses

While Gemini SH is designed to pass the response of functions directly to the Gemini language model, there is the possibility of expanding the system to handle responses differently. This allows for greater flexibility and control over the agent's behavior.

**How to add new `response_to_agent` actions:**

To add new actions that the system can interpret in the `response_to_agent` key of the function's return dictionary, modifications must be made in two main areas:

**1. The `FunctionManager`:**

- **`handle_functions_response(self, response)`:** This function in `function_manager.py` is responsible for processing the responses from functions. A new `if` block must be added to handle the new action. For example, if you want to add an action called `display_message`, the following code would be added:

```python
def handle_functions_response(self, response):
    # ... existing code ...

    if 'display_message' in response:
        self.output_manager.print(response['display_message'])

    # ... existing code ...
```

**2. Custom Functions:**

- **Function Return:** Functions that wish to use the new action must include it in the `response_to_agent` dictionary. For example:

```python
def my_custom_function():
    # ... function code ...

    return {
        "response_to_agent": {"display_message": "This message will be displayed on the console."}
    }
```

**Concrete Example: Displaying a Message on the Console:**

Suppose you want to create a function that displays a message on the console without sending it to the language model. You could create a function like the following:

```python
def show_console_message(message):
    """
    Displays a message on the console without sending it to the model.

    Args:
        message (str): The message to display.

    Returns:
        dict: A dictionary with an instruction for the agent.
    """
    return {
        "response_to_agent": {"display_message": message}
    }
```

Then, the handling of the `display_message` action must be added in the `handle_functions_response` function of the `FunctionManager`, as shown above.

**In summary, expanding Gemini SH to handle function responses in a customized way involves:**

1. **Defining the new action:** Identify the specific action you want to perform with the function's response.
2. **Modifying the `FunctionManager`:** Add the necessary code to handle the new action in the `handle_functions_response` function.
3. **Adapting the functions:** Modify the functions that will use the new action to include it in the `response_to_agent` dictionary.

This process allows for greater flexibility and control over the agent's behavior, opening up the possibility of integrating new functionalities and adapting the system to specific needs.

## Function Construction and Dynamic Loading in Gemini SH: A Detailed Analysis

Functions in Gemini SH are defined in Python files within the `.geminiSH/functions` folder. Each file can contain one or more functions, and the way these functions are constructed is crucial for their correct integration with the system.

**Structure of a Function:**

1. **Documentation (Docstring):** Each function must begin with a docstring that describes its purpose, parameters, return value, and when it should be used. This docstring is fundamental for the Gemini language model to understand the function and use it appropriately.

2. **Function Code:** The function code should be clear, concise, and well-documented with comments. It's important to follow programming best practices to ensure code readability and maintainability.

3. **Function Return:** The function's return type determines how the system will process the response:

   - **`str` (text string):** The string is sent directly to the language model as part of the response. This is the simplest return type and is used for informative responses or error messages.

   - **`dict` (dictionary):** The dictionary can contain two keys: `response` and `response_to_agent`.
     - `response`: A text string that is sent to the language model as part of the response.
     - `response_to_agent`: A dictionary with instructions for the agent. These instructions can include:
       - `files_to_upload`: A list of file paths that will be uploaded to Google Gemini.
       - `load_chat_history`: The ID of a chat that will be loaded from the history.
       - `require_execution_result`: A boolean value that indicates whether the function's result should be sent immediately to the model (True) or if it should wait for the next user interaction (False).

**Example of a Function:**

```python
def get_content_file(file_path):
    """
    Processes a file and obtains its content.
    If the user wants to work with a file, this function is executed first.

    Args:
        file_path (str): File path.

    Returns:
        dict: A dictionary with the response for the user and an instruction for the agent.
    """
    # ... function code ...

    return {
        "response": "The file has been processed successfully.",
        "response_to_agent": {"files_to_upload": [file_path], 'require_execution_result': True}
    }
```

**Dynamic Function Loading:**

The system loads functions dynamically from the `.geminiSH/functions` folder. This means that it is not necessary to restart the system for new functions to be available. However, it is important to keep in mind that:

## Expanding Gemini SH: Custom Handling of Function Responses

While Gemini SH is designed to pass the response of functions directly to the Gemini language model, there is the possibility of expanding the system to handle responses differently. This allows for greater flexibility and control over the agent's behavior.

**How to add new `response_to_agent` actions:**

To add new actions that the system can interpret in the `response_to_agent` key of the function's return dictionary, modifications must be made in two main areas:

**1. The `FunctionManager`:**

- **`handle_functions_response(self, response)`:** This function in `function_manager.py` is responsible for processing the responses from functions. A new `if` block must be added to handle the new action. For example, if you want to add an action called `display_message`, the following code would be added:

```python
def handle_functions_response(self, response):
    # ... existing code ...

    if 'display_message' in response:
        self.output_manager.print(response['display_message'])

    # ... existing code ...
```

**2. Custom Functions:**

- **Function Return:** Functions that wish to use the new action must include it in the `response_to_agent` dictionary. For example:

```python
def my_custom_function():
    # ... function code ...

    return {
        "response_to_agent": {"display_message": "This message will be displayed on the console."}
    }
```

**Concrete Example: Displaying a Message on the Console:**

Suppose you want to create a function that displays a message on the console without sending it to the language model. You could create a function like the following:

```python
def show_console_message(message):
    """
    Displays a message on the console without sending it to the model.

    Args:
        message (str): The message to display.

    Returns:
        dict: A dictionary with an instruction for the agent.
    """
    return {
        "response_to_agent": {"display_message": message}
    }
```

Then, the handling of the `display_message` action must be added in the `handle_functions_response` function of the `FunctionManager`, as shown above.

**In summary, expanding Gemini SH to handle function responses in a customized way involves:**

1. **Defining the new action:** Identify the specific action you want to perform with the function's response.
2. **Modifying the `FunctionManager`:** Add the necessary code to handle the new action in the `handle_functions_response` function.
3. **Adapting the functions:** Modify the functions that will use the new action to include it in the `response_to_agent` dictionary.
