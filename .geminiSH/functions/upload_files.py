import mimetypes
from datetime import datetime, timedelta
import google.generativeai as genai
from rich.console import Console

console = Console()

SUPPORTED_MIME_TYPES = [
    "text/plain",
    "application/pdf",
    "audio/mpeg",
    "audio/wav",
    "video/mp4",
    "image/jpeg",
    "image/png",
]

def upload_files(file_paths: list, expiry_time: str = '') -> dict | str:
    """
    Upload multiple files to Google Gemini and return the response. If you only want to upload a single file, you can pass a single file path inside a list.

    Parameters:
    file_paths (list): List of file paths to be uploaded.
    expiry_time (str): The expiration time for the files in ISO format. Defaults to 48 hours from now. If the user doesn't provide an expiry time do not set it.

    Returns:
    files: The uploaded files.
    """
    uploaded_files = []
    responses = []

    for file_path in file_paths:
        mime_type, _ = mimetypes.guess_type(file_path)
        

        if mime_type in SUPPORTED_MIME_TYPES:
            with console.status("[bold yellow]Gemini is uploading a file...[/bold yellow]"):
                response = genai.upload_file(file_path)
                responses.append(response)      

            if not expiry_time:
                expiry_time = (datetime.now() + timedelta(hours=48)).isoformat()

            file_data = response.to_dict()
            file_data = {
                "uri": file_data['uri'],
                "mime_type": file_data['mime_type'],
                "expiry_time": expiry_time,
                "creation_time": datetime.now().isoformat(),
                "original_path": file_path
            }
            uploaded_files.append(file_data)
        else:
            return f"[error]Unsupported file type: {file_path}[/error]"

    return {
        "response": "Files uploaded successfully.",
        "response_to_agent": {"files": uploaded_files, 'require_execution_result': True}
    }
