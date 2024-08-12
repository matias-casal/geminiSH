"""
This module provides functionality to apply unified git diffs to text-based files.
"""
import os
import unidiff

from output_manager import OutputManager

output_manager = OutputManager()


def apply_diff_changes(file_path, diff_text):
    """
    Use this function to apply modifications to text-based files, especially programming files.
    Send changes as a unified git diff to a specific file.
    After this function is executed, the file will be modified.

    Args:
        file_path (str): The path to the file to which the diff will be applied.
        diff_text (str): The diff text in unified format.

    Returns:
        str: The result of the operation.
    """
    try:
        # Read the original file content
        if not os.path.exists(file_path):
            return f"[error]The file {file_path} does not exist.[/error]"

        with open(file_path, "r", encoding="utf-8") as file:
            original_content = file.readlines()

        # Parse the diff
        diff = unidiff.PatchSet(diff_text)

        # Apply the diff to the original content
        modified_content = original_content[:]
        for patched_file in diff:
            if patched_file.path != file_path:
                return f"[error]The diff does not correspond to the specified file.[/error]"

            for hunk in patched_file:
                for line in hunk:
                    if line.is_added:
                        modified_content.insert(line.target_line_no - 1, line.value)
                    elif line.is_removed:
                        del modified_content[line.source_line_no - 1]

        # Save the modified content back to the file
        with open(file_path, "w", encoding="utf-8") as file:
            file.writelines(modified_content)

        return f"The file {file_path} has been modified successfully."
    except Exception as e:
        output_manager.print(e)
        return f"[error]An error occurred while modifying the file: {str(e)}[/error]"
    