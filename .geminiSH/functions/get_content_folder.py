import os
import mimetypes
from rich.console import Console

console = Console()

DEBUG = os.getenv('DEBUG')

SUPPORTED_MIME_TYPES = [
    "application/pdf",
    "audio/mpeg",
    "audio/wav",
    "video/mp4",
    "image/jpeg",
    "image/png",
]

def get_content_of_folder(directory_path):
    """
    Processes files in a directory and get the content. If the user want to work with a folder, execute this function.

    Parameters:
    directory_path (str): The path of the directory to process.

    Returns:
    str | file: Contains text content from readable files and the copatible files.
    """
    text_files_content = {}
    files_to_upload = []
    num_bytes=1024
    
    try:
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                full_path = os.path.join(root, file)
                
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        f.read(num_bytes)
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    content = f"---Start of file {file}---\n{content}\n---End of file {file}---"
                    text_files_content[full_path] = content
                except (UnicodeDecodeError, IOError):
                    mime_type, _ = mimetypes.guess_type(full_path)
                    if mime_type in SUPPORTED_MIME_TYPES:
                        files_to_upload.append(full_path)
        
        return {
            "response": "All the compatible files are ready, follow the user instructions.",
            "response_to_agent": {"text_files_content": text_files_content, "files_to_upload": files_to_upload, 'require_execution_result': True}
        }
    
    except Exception as e:
        if DEBUG:
            console.print(f"[bold red]{type(e).__name__}: {str(e)}[/bold red]")
        return "[error]An error occurred while processing the files[/error]"
