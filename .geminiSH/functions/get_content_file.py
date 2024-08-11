import os
import mimetypes
from output_manager import OutputManager

output_manager = OutputManager()

DEBUG = os.getenv('DEBUG')

SUPPORTED_MIME_TYPES = [
    "application/pdf",
    "audio/mpeg",
    "audio/wav",
    "video/mp4",
    "image/jpeg",
    "image/png",
]

def get_content_file(file_path):
    """
    Processes a single file and get the content.
    If the user want to work with a single file, execute this function first, and wait for the response.

    Parameters:
    file_path (str): The absolute path of the file to process.
    num_bytes (int): Number of bytes to read from the file to determine if it's a readable text file.

    Returns:
    str | file: Contains the text content if readable, or the file.
    """
    num_bytes = 1024
    try:
        with output_manager.managed_status("[bold yellow]Processing file...[/bold yellow]"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    f.read(num_bytes)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                content = f"---Start of file {os.path.basename(file_path)}---\n{content}\n---End of file {os.path.basename(file_path)}---"
                return {
                    "response": content,
                    "response_to_agent": {'require_execution_result': True}
                }
            except (UnicodeDecodeError, IOError):
                mime_type, _ = mimetypes.guess_type(file_path)
                if mime_type in SUPPORTED_MIME_TYPES:
                    return {
                        "response": "The file is ready, follow the user instructions.",
                        "response_to_agent": {"files_to_upload": [file_path], 'require_execution_result': True}
                    }
                else:
                    return {
                        "response": "File is not supported.",
                        "response_to_agent": {'require_execution_result': False}
                    }
    except Exception as e:
        if DEBUG:
            output_manager.print(e)
        return "[error]An error occurred while processing the file[/error]"