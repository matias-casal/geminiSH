"""
This module provides functionality to upload files to Google Gemini. It includes a function
to upload multiple files, with options for setting expiration times and forcing uploads
even if the files are already cached. The module also handles MIME type validation and
cache management.
"""

import os
import mimetypes
import json
from datetime import datetime, timedelta
import google.generativeai as genai
from output_manager import OutputManager

output_manager = OutputManager()

USE_CACHE = False


def upload_files(file_paths: list, expiry_time: str = "", force_upload: bool = False) -> dict | str:
    """
    Upload multiple files to Google Gemini and return the response. If you only want to upload a 
    single file, you can pass a single file path inside a list.

    Parameters:
    file_paths (list): List of file paths to be uploaded.
    expiry_time (str): The expiration time for the files in ISO format. Defaults to 48 hours from 
                       now. If the user doesn't provide an expiry time do not set it.
    force_upload (bool): If True, the files will be uploaded even if they are already in the cache, 
                         only add when the user request to upload again.

    Returns:
    files: The uploaded files.
    """
    supported_mime_types = output_manager.config_manager.config["MODEL_SUPPORTED_MIME_TYPES"]
    uploaded_files = []
    responses = []

    for file_path in file_paths:
        mime_type, _ = mimetypes.guess_type(file_path)

        if mime_type not in supported_mime_types:
            return f"[error]Unsupported file type: {file_path}[/error]"

        # Check and create cache.json if it doesn't exist
        if (
            not output_manager.config_manager.config["REMOVE_CACHE_AFTER_LOAD"]
            and not force_upload
            and USE_CACHE
        ):
            cache_file_path = os.path.join(os.path.dirname(__file__), "..", "cache.json")
            if not os.path.exists(cache_file_path):
                with open(cache_file_path, "w", encoding="utf-8") as cache_file:
                    json.dump([], cache_file)

            # Load existing cache data
            with open(cache_file_path, "r", encoding="utf-8") as cache_file:
                cache_data = json.load(cache_file)

            # Check if file is already in cache and not expired
            cached_file = next(
                (
                    item
                    for item in cache_data
                    if item["original_path"] == file_path
                    and datetime.fromisoformat(item["expiry_time"]) > datetime.now()
                ),
                None,
            )
            if cached_file:
                cached_file["uri"] = cached_file["uri"]
                output_manager.debug(f"File found in cache: {cached_file}")
                uploaded_files.append(cached_file)
                continue

        with output_manager.managed_status(
            "[bold yellow]Gemini is uploading a file...[/bold yellow]"
        ):
            response = genai.upload_file(file_path)
            responses.append(response)

        if not expiry_time:
            expiry_time = (datetime.now() + timedelta(hours=48)).isoformat()

        file_data = response.to_dict()
        file_data = {
            "uri": file_data["uri"],
            "mime_type": file_data["mime_type"],
            "expiry_time": expiry_time,
            "creation_time": datetime.now().isoformat(),
            "original_path": file_path,
        }
        output_manager.debug(f"Uploading file: {file_data}")
        uploaded_files.append(file_data)

        if output_manager.config_manager.config["REMOVE_CACHE_AFTER_LOAD"]:
            os.remove(file_path)
        elif USE_CACHE:
            # Append new file data to cache
            cache_data.append(file_data)

            # Save updated cache data
            with open(cache_file_path, "w", encoding="utf-8") as cache_file:
                json.dump(cache_data, cache_file, indent=4)

    output_manager.debug(f"Uploaded files: {uploaded_files}")
    return {"response_to_agent": {"files": uploaded_files, "require_execution_result": True}}
