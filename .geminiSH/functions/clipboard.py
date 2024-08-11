import os
import pyperclip
from output_manager import OutputManager

output_manager = OutputManager()
DEBUG = os.getenv('DEBUG')

def clipboard(action="get", content=None):
    """
    Manages clipboard operations such as getting and setting content.
    If you want to set, you need to pass the content as a parameter.
    Also you can request the user to copy the content that you need.
    
    Parameters:
    action (str) 'get' | 'set': The action to perform. Either "get" to retrieve clipboard content or "set" to set content.
    content (str, optional): The content to set in the clipboard if the action is "set".

    Returns:
    str: In the case of get, the content of the clipboard and it the case of set a message indicating the action was successful or not.
    """
    try:
        if action == "get":
            clipboard_content = pyperclip.paste()
            return clipboard_content

        elif action == "set" and content is not None:
            pyperclip.copy(content)
            return "Clipboard content set successfully."
        else:
            return "[error]Invalid action or missing content for setting the clipboard.[/error]"
    
    except Exception as e:
        if DEBUG:
            output_manager.print(e)
        return "[error]An error occurred while managing the clipboard[/error]"