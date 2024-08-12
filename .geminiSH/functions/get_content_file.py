"""
This module provides functionality to retrieve the content of a single file 
for the GeminiSH application.
"""

import os
import mimetypes
from output_manager import OutputManager

output_manager = OutputManager()

DEBUG = os.getenv("DEBUG")

def get_content_file(file_path):
    """
    Processes a single file and gets the content.
    If the user wants to work with a single file, execute this function first.

    Parameters:
    file_path (str): The absolute path of the file to process.

    Returns:
    str | file: Contains the text content if readable, or the file.
    """
    num_bytes = 1024
    supported_mime_types = output_manager.config_manager.config["MODEL_SUPPORTED_MIME_TYPES"]
    try:
        with output_manager.managed_status("[bold yellow]Processing file...[/bold yellow]"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    f.read(num_bytes)
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    
                file_name = os.path.basename(file_path)
                content = [f"---Start of file {file_name}---"]
                content.extend(lines)
                content.append(f"---End of file {file_name}---")
                content_str = "".join(content)
                return {
                    "response": content_str,
                    "response_to_agent": {"require_execution_result": True},
                }
            except (UnicodeDecodeError, IOError):
                mime_type, _ = mimetypes.guess_type(file_path)
                if mime_type in supported_mime_types:
                    return {
                        "response_to_agent": {
                            "files_to_upload": [file_path],
                            "require_execution_result": True,
                        }
                    }
                else:
                    return {
                        "response": "File is not supported.",
                        "response_to_agent": {"require_execution_result": False},
                    }
    except Exception as e:
        if DEBUG:
            output_manager.print(e)
        return "[error]An error occurred while processing the file[/error]"