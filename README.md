## Gemini SH: Your Personalized AI Agent for Enhanced Productivity

**Gemini SH** is a powerful Python library that leverages the capabilities of Google Gemini to create personalized AI agents capable of executing diverse functions on your computer, extending far beyond simple terminal interactions. Imagine having a versatile assistant that can understand your natural language commands and execute complex tasks, from managing files and automating workflows to generating content and even interacting with your codebase.

### A Dynamic, Agent-Based Approach

One of the core strengths of Gemini SH lies in its dynamic agent-based architecture. Depending on where you run the `geminiSH` command, you can create specialized agents tailored to specific tasks and environments. Here's how it works:

- **Agent Creation**: When you execute the command within a directory, a `.geminiSH` folder is automatically created in that location. This folder serves as the agent's workspace, housing its configuration, history, and custom functions.
- **Agent Configuration**: Each agent can be uniquely configured, allowing you to customize everything from the model used (e.g., `gemini-1.5-pro-latest`) to the maximum number of output tokens expected. This customization can even be done through natural language interactions with the model itself.
- **Function Expansion**: Within the `.geminiSH` folder, you can create a `functions` directory to define custom Python functions that expand the agent's capabilities.
- **Specialized Agents**: This dynamic structure empowers you to create specialized agents for different purposes. For instance, you can create an agent dedicated to code modification with a tailored system prompt and instructions, effectively building a coding assistant within your development environment.

### Core Features

- **Interactive Chat**: Engage in natural language conversations with the Gemini language model through your terminal.
- **Function Execution**: Gemini SH can execute user-defined Python functions, extending its capabilities beyond basic chat interactions.
- **Cross-Platform Compatibility**: Designed to run seamlessly on any terminal and operating system.
- **Turn-Based Chat System**: Conversations are structured in turns, allowing for clear communication and back-and-forth interactions.
- **Customizable Functions**: Extend Gemini SH's capabilities by adding Python scripts with functions defined in the `functions` directory.
- **Rich Function Descriptions**: Use docstrings to provide detailed information about each function, including its purpose, parameters, return values, and when it should be executed.
- **Specialized Function Responses**: Functions can return different types of responses, including:
  - **Standard String Responses**: Returned directly to the model as a text message.
  - **`response` Object**: An object containing a `response` field, which is passed to the model as a text message, and a `response_to_agent` field, which triggers specific actions within Gemini SH.
  - **Actionable Responses**: The `response_to_agent` field can contain instructions like:
    - `files_to_upload`: A list of file paths that will automatically trigger the `upload_files` function for each file.
    - `require_execution_result: True`: Indicates that the function's results should be immediately sent back to the model upon completion, bypassing user interaction.
- **System Instructions and Configuration**:
  - `prompts/system_instructions.md`: Contains the initial instructions for the Gemini model, defining its role and behavior.
  - `config.json`: Configure various system settings, including the Gemini model to use and saving options.
- **Persistent Chat History**: Conversations are saved in `history.json` for future reference and analysis.
- **Command-Line Function Execution**: Execute functions directly from the command line by passing the function name and its arguments as arguments when running Gemini SH.
- **First-Time User Guidance**: A helpful message explaining the system's functionalities and usage is displayed during initial runs.
- **Modular Managers**: The codebase is structured around several managers that handle specific aspects of the system (config, state, input, output, chat, function, and model).

### Use Cases

Gemini SH opens up a world of possibilities for interacting with your computer:

- **File Management**: Organize and process files based on user requests.
- **Code Interaction**: Get help with coding errors, generate code snippets, and even modify source files directly through diffs.
- **System Automation**: Automate repetitive tasks and workflows through custom functions and Bash commands.
- **Content Creation**: Generate presentations and other content based on text input.
- **Information Retrieval**: Get answers to questions based on the content of local files and documentation.
- **Voice Interaction**: Record audio and send it to Gemini, enabling hands-free communication.
- **Visual Context Awareness**: Take screenshots to provide Gemini with visual context for more relevant responses.
- **Cross-Application Integration**: Use the clipboard to exchange data with other applications.

## How to Install and Use Gemini SH (Updated)

This guide will walk you through the steps to install and start using Gemini SH, your personalized AI agent for enhanced productivity.

**Prerequisites:**

- **Python 3.6 or higher:** Gemini SH requires Python 3.6 or a later version to run. You can check your Python version by running `python --version` or `python3 --version` in your terminal.

- **PIP (Package Installer for Python):** PIP is typically included with Python installations. You can verify its presence by running `pip --version` or `pip3 --version`.

**Installation Steps:**

1. **Clone the Repository:**

   You can clone the Gemini SH repository from GitHub using the following command in your terminal:

   ```bash
   git clone https://github.com/matias-casal/geminiSH.git
   ```

2. **Navigate to the Directory:**

   After cloning, navigate to the `geminiSH` directory:

   ```bash
   cd geminiSH
   ```

3. **Install Gemini SH:**

   Install Gemini SH and its dependencies using PIP:

   ```bash
   pip install .
   ```

   Alternatively, you can install it directly from the cloned directory using:

   ```bash
   pip install geminish
   ```

4. **Set Your API Key:**

   You need a Google Gemini API key to use Gemini SH. You can obtain one from the Google AI Studio. Once you have your API key, set it in the `config.json` file located in the `.geminiSH` directory:

   ```json
   {
     "GOOGLE_API_KEY": "YOUR_API_KEY_HERE"
     // ... other configurations
   }
   ```

   Alternatively, you can set the API key as an environment variable:

   ```bash
   export GOOGLE_API_KEY="YOUR_API_KEY_HERE"
   ```

**Using Gemini SH:**

1. **Start the Interactive Chat:**

   To start the interactive chat session, run the following command in your terminal:

   ```bash
   geminiSH
   ```

2. **Interact with the Agent:**

   You can now interact with the Gemini SH agent using natural language. You can ask questions, give commands, and even execute custom functions.

3. **Execute Functions Directly:**

   You can also execute functions directly from the command line. For example, for give voice commands execute the `record` function with a specific file path:

   ```bash
   geminiSH record
   ```

4. **Add Custom Functions**:
   - Create Python scripts in the `functions` directory, defining your desired functions.
   - Use docstrings to provide clear and comprehensive descriptions of each function for the model to understand.

### Contributing

Contributions to Gemini SH are welcome! You can contribute by:

- **Adding New Functions**: Expand the system's capabilities by creating new Python functions for specific tasks.
- **Improving Documentation**: Enhance the README, docstrings, and comments for better clarity and understanding.
- **Fixing Bugs and Issues**: Help maintain and improve the codebase by addressing any reported issues.
- **Sharing Ideas and Use Cases**: Contribute to the project's growth by sharing your ideas and potential applications.

### Future Directions

- **Voice Recognition**: Integrate with voice recognition libraries for seamless voice-based interactions.
- **GUI Integration**: Explore options for integrating Gemini SH with a graphical user interface for a more user-friendly experience.
- **Plugin System**: Develop a plugin system to enable users to easily extend the system's functionalities without modifying the core codebase.
- **Enhanced Context Awareness**: Explore techniques for providing Gemini with more context from the user's system, such as active applications, recent files, and browser history.

### Acknowledgements

This project is inspired by the power and flexibility of Google Gemini and the potential it holds for revolutionizing human-computer interaction.
