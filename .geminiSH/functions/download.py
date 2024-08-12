import os
import mimetypes
import urllib.request
from rich.console import Console
from rich.progress import (
    Progress,
    BarColumn,
    DownloadColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from output_manager import OutputManager

output_manager = OutputManager()

DEBUG = os.getenv('DEBUG')

progress = Progress(
    TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
    BarColumn(bar_width=None),
    "[progress.percentage]{task.percentage:>3.1f}%",
    "•",
    DownloadColumn(),
    "•",
    TransferSpeedColumn(),
    "•",
    TimeRemainingColumn(),
)

def download(url: str):
    """
    Download the content or the file of the given url.
    If the user give you a url, use this function to analize the content of it.

    Parameters:
    url (str): The url of the web or file to download.
    
    Returns:
    str | file: Contains the text content if readable, or the file.
    """
    SUPPORTED_MIME_TYPES = output_manager.config_manager.config["MODEL_SUPPORTED_MIME_TYPES"]
    try:
        filename = url.split("/")[-1]
        response = urllib.request.urlopen(url)
        mime_type, _ = mimetypes.guess_type(url)
        
        # Check MIME type and process accordingly
        if mime_type and mime_type in SUPPORTED_MIME_TYPES:
            dest_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'cache', filename)
            task_id = progress.add_task("download", filename=filename, start=False)
            
            with output_manager.managed_status("[bold yellow]Downloading file...[/bold yellow]"):
                with progress:
                    with open(dest_path, "wb") as dest_file:
                        total_size = int(response.info().get("Content-length", 0))
                        progress.update(task_id, total=total_size)
                        progress.start_task(task_id)
                        
                        for data in iter(lambda: response.read(32768), b""):
                            dest_file.write(data)
                            progress.update(task_id, advance=len(data))
            
            return {
                "response": "The file is ready, uset it.",
                "response_to_agent": {"files_to_upload": [dest_path], 'require_execution_result': True}
            }
        
        elif mime_type and "text" in mime_type:
            content = response.read().decode('utf-8')
            content = f"---Start content of web: {url}---\n{content}\n---End of content of web---"
            return content
            
        else:
            return "The content of the url is not supported."
            
    except Exception as e:
        if DEBUG:
            output_manager.print(e)
        return "[error]An error occurred while processing the URL[/error]"