"""
This module provides functionality to retrieve system documentation and 
information about the system for the GeminiSH application.
"""

import os

def get_system_documentation():
    """
    Get the system documentation and information about the system.
    If the user ask somethin about how you work then use this function.
    If the user ask something about how to create a new function or expand the sistem.

    Parameters:
    get_all_information (bool, optional): If True, get all the information. Default is False.

    Returns:
    str: The system documentation and information about the system.
    """
    file_path_system_documentation = "../prompts/system_explanined.md"
    content = ""
    if os.path.exists(file_path_system_documentation):
        with open(file_path_system_documentation, "r", encoding="utf-8") as file:
            content = file.read()
    else:
        return "[error]The system documentation file does not exist.[/error]"
    return content
