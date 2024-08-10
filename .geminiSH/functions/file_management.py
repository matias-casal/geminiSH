import os

def create_file(file_path: str, content: str = ''):
    """
    Create a new file with optional initial content.

    Parameters:
    file_path (str): The path to the file where lines will be replaced.
    content (str): The content to insert in place of the specified lines.

    Returns:
    str: A message indicating the file has been created.
    """
    with open(file_path, 'w') as file:
        file.write(content)
    return f"[file_created]{file_path}[/file_created]"


def delete_file(file_path: str):
    """
    Delete a file at a specified path.

    Parameters:
    file_path (str): The path to the file that will be deleted.

    Returns:
    str: A message indicating the file has been deleted.
    """
    os.remove(file_path)
    return f"[file_deleted]{file_path}[/file_deleted]"

