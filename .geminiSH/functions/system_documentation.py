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
    file_path_system_documentation = '../prompts/system_explanined.md'
    file_path_system_expand_instructions = '../prompts/system_expand_instructions.md'
    content = ""
    if os.path.exists(file_path_system_documentation):
        with open(file_path_system_documentation, 'r') as file:
            content = file.read()
    else:
        return "[error]The system documentation file does not exist.[/error]"
    return content