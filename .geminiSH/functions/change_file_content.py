import unidiff
import os
from output_manager import OutputManager

output_manager = OutputManager()

def change_file_content(file_path, diff_text):
    """
    Use this function to apply a unified git diff to a specific file, especially when working with programming files
    or any text-based files. It is particularly useful when you have a patch or diff that needs to be applied to source 
    code or configuration files. If you can explain to the user the change.

    Do Not Use When:
        To add, edit, or remove text from a file.

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
        
        with open(file_path, 'r') as file:
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
        with open(file_path, 'w') as file:
            file.writelines(modified_content)
        
        return f"The file {file_path} has been modified successfully."
    except Exception as e:
        output_manager.print(e)
        return f"[error]An error occurred while modifying the file: {str(e)}[/error]"
