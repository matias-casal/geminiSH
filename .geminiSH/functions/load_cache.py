import os
import json
from datetime import datetime
from output_manager import OutputManager

output_manager = OutputManager()

def load_files_from_cache(mime_type_filter=None, load_nth_last=None):
    """
    Load files from cache and return their data. If files are expired, check if they still exist and reload them.

    Parameters:
    mime_type_filter (str, optional): MIME type to filter the files.
    load_nth_last (int, optional): Number of last files to load from cache.

    Returns:
    dict: The loaded files data.
    """
    cache_file_path = os.path.join(os.path.dirname(__file__), '..', 'cache.json')
    
    if not os.path.exists(cache_file_path):
        return f"[error]The cache file {cache_file_path} does not exist.[/error]"

    with open(cache_file_path, 'r') as cache_file:
        cache_data = json.load(cache_file)

    valid_files = []
    expired_files = []

    for file_data in cache_data:
        expiry_time = datetime.fromisoformat(file_data['expiry_time'])
        if datetime.now() > expiry_time:
            if os.path.exists(file_data['original_path']):
                expired_files.append(file_data)
            continue

        if mime_type_filter and file_data['mime_type'] != mime_type_filter:
            continue

        valid_files.append(file_data)

    if load_nth_last is not None:
        valid_files = valid_files[-load_nth_last:]

    if expired_files:
        return {
            "response": "Some files have expired but still exist. Reloading them.",
            "response_to_agent": {"files_to_upload": expired_files, 'require_execution_result': True}
        }

    return {
        "response": "The files are ready, follow the user instructions.",
        "response_to_agent": {"files": valid_files, 'require_execution_result': True}
    }