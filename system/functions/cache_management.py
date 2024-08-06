# system/functions/cache_management.py
import os
import datetime
import mimetypes
import google.generativeai as genai
from rich.console import Console

console = Console()

# MIME Types supported by Gemini
SUPPORTED_MIME_TYPES = [
    "text/plain",
    "application/pdf",
    "audio/mpeg",
    "audio/wav",
    "video/mp4",
    "image/jpeg",
    "image/png",
]

def upload_to_cache(document_path: str, ttl: int, display_name: str = "", description: str = "") -> str:
    """
    ## File Caching
    - You can cache files using the `upload_to_cache` function. This function takes three arguments:
        - `document_path`: The path to the document you want to cache.
        - `ttl`: Time to live for the cached file in seconds.
        - `display_name`: A display name for the document (optional).
        - `description`: A short description of the document (optional).
    - You should use this function whenever the user requests to work with a local file.

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