# system/functions/file_analysis.py
import os
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

def upload_and_describe_file(file_path: str) -> genai.types.File:
    """
    Uploads a file using genai.upload_file and returns the uploaded file object. 
    The object can be used by other functions for analysis.

    Parameters:
    file_path (str): The path to the file to upload.

    Returns:
    genai.types.File: The uploaded file object.

    Raises:
    FileNotFoundError: If the file does not exist at the specified path.
    TypeError: If the file type is not supported.
    RuntimeError: If there is an error during the file upload.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Error: File not found: {file_path}")

    mime_type, _ = mimetypes.guess_type(file_path)

    if mime_type not in SUPPORTED_MIME_TYPES:
        raise TypeError(
            f"Error: Unsupported file type: {mime_type}. Supported types are: {SUPPORTED_MIME_TYPES}"
        )

    try:
        uploaded_file = genai.upload_file(file_path)
        console.print(
            f"Document '{file_path}' uploaded successfully as '{uploaded_file.name}'.",
            style="bold green",
        )
        return uploaded_file
    except Exception as e:
        raise RuntimeError(f"Error uploading file: {e}")

