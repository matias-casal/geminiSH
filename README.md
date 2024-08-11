## Gemini SH: An Intelligent Terminal Assistant Powered by Google Gemini

**Gemini SH** is a Python library designed to transform your terminal into an intelligent assistant powered by the advanced capabilities of Google Gemini. This project aims to bridge the gap between natural language and terminal commands, allowing users to interact with their computers intuitively and efficiently without needing to be terminal experts.

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

### Getting Started

1. **Install Dependencies**: Ensure you have the required Python libraries installed. You can find a list of dependencies in the `requirements.txt` file (to be created).
2. **Configure Gemini SH**:
   - Set your Google Gemini API key in `config.json` or as an environment variable (`GOOGLE_API_KEY`).
   - Customize the `system_instructions.md` file with your desired prompts and guidelines for the Gemini model.
   - Configure other system settings in `config.json` as needed.
3. **Add Custom Functions**:
   - Create Python scripts in the `functions` directory, defining your desired functions.
   - Use docstrings to provide clear and comprehensive descriptions of each function for the model to understand.
4. **Run Gemini SH**:
   - Execute `python main.py` to start the interactive chat session.
   - Alternatively, execute `python main.py <function_name> <arguments>` to directly execute a function from the command line.

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
