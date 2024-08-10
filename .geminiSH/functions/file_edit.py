def replace_lines(file_path: str, start_line: int, end_line: int, content: str):
    """
    Replace lines in a file from start_line to end_line with the provided content. Return the original lines that were replaced.

    Parameters:
    file_path (str): The path to the file where lines will be replaced.
    start_line (int): The starting line number for the replacement (1-based index).
    end_line (int): The ending line number for the replacement (1-based index).
    content (str): The content to insert in place of the specified lines.

    Returns:
    str: A message indicating the original lines that were replaced.
    """
    with open(file_path, 'r') as file:
        lines = file.readlines()
    # Capture the lines that will be replaced
    replaced_lines = lines[start_line-1:end_line]
    lines[start_line-1:end_line] = [content + '\n']
    with open(file_path, 'w') as file:
        file.writelines(lines)
    return f"[replaced_lines]{replaced_lines}[/replaced_lines]"


def insert_lines(file_path: str, start_line: int, content: str):
    """
    Insert lines into a file at the specified line number. Return the line that was inserted.

    Parameters:
    file_path (str): The path to the file where lines will be inserted.
    start_line (int): The line number at which the content will be inserted (1-based index).
    content (str): The content to insert into the file.

    Returns:
    str: A message indicating the line that was inserted.
    """
    with open(file_path, 'r') as file:
        lines = file.readlines()
    lines.insert(start_line - 1, content + '\n')
    with open(file_path, 'w') as file:
        file.writelines(lines)
    # Return the line that was inserted
    return f"[inserted_line]{lines[start_line - 1]}[/inserted_line]"


def delete_lines(file_path: str, start_line: int, end_line: int):
    """
    Delete lines from a file from start_line to end_line. Return the original lines that were deleted.

    Parameters:
    file_path (str): The path to the file where lines will be deleted.
    start_line (int): The starting line number for the deletion (1-based index).
    end_line (int): The ending line number for the deletion (1-based index).

    Returns:
    str: A message indicating the original lines that were deleted.
    """
    with open(file_path, 'r') as file:
        lines = file.readlines()
    # Capture the lines that will be deleted
    deleted_lines = lines[start_line-1:end_line]
    del lines[start_line-1:end_line]
    with open(file_path, 'w') as file:
        file.writelines(lines)
    # Return the lines that were deleted
    return f"[deleted_lines]{deleted_lines}[/deleted_lines]"

