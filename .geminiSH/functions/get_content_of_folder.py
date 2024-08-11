import os
import mimetypes
from rich.console import Console
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

def get_content_of_folder(directory_path, recursive=True):
    """
    Processes a directory and get the content. 
    If the user wants to work with a folder or it refers to a content of a folder, execute this function first, and wait for the response.

    Parameters:
    directory_path (str): The path of the directory to process. Do not inclute '*'.
    recursive (bool): Whether to process directories recursively. Default is True.

    Returns:
    str | file: Contains text content from readable files and the compatible files.
    """
    text_files_content = {}
    files_to_upload = []
    num_bytes = 1024
    
    try:
        for root, dirs, files in os.walk(directory_path):
            # Exclude directories based on SCRAPE_DATA_RULES
            dirs[:] = [d for d in dirs if d not in SCRAPE_DATA_RULES["exclude_directories"]]
            
            if not recursive:
                # If not recursive, clear dirs to prevent os.walk from going deeper
                dirs.clear()
            
            for file in files:
                # Exclude files based on SCRAPE_DATA_RULES
                if file in SCRAPE_DATA_RULES["exclude_filenames"] or any(file.endswith(ext) for ext in SCRAPE_DATA_RULES["exclude_extensions"]):
                    continue
                
                full_path = os.path.join(root, file)
                
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        f.read(num_bytes)
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    text_files_content[full_path] = content
                except (UnicodeDecodeError, IOError):
                    mime_type, _ = mimetypes.guess_type(full_path)
                    if mime_type in SUPPORTED_MIME_TYPES:
                        files_to_upload.append(full_path)
                        text_files_content[full_path] = "File uploaded."
        
        return {
            "response": text_files_content,
            "response_to_agent": {"files_to_upload": files_to_upload, 'require_execution_result': True} if files_to_upload else None
        }
    
    except Exception as e:
        if DEBUG:
            output_manager.print(e)
        return "[error]An error occurred while processing the files[/error]"
    
    
SCRAPE_DATA_RULES = {
    "exclude_filenames": [".DS_Store"],
    "exclude_extensions": [
      ".gif",
      ".bmp",
      ".tiff",
      ".ico",
      ".exe",
      ".dll",
      ".so",
      ".o",
      ".a",
      ".obj",
      ".lib",
      ".pdb",
      ".class",
      ".jar",
      ".war",
      ".ear",
      ".bin",
      ".dat",
      ".db"
    ],
    "exclude_directories": [
      "ignore_folder",
      ".git",
      ".svn",
      ".hg",
      "node_modules",
      "bower_components",
      "dist",
      "build",
      "bin",
      "obj",
      "out",
      "__pycache__"
    ]
}