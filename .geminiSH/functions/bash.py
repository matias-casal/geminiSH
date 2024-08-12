"""
This module provides functionality to execute bash commands 
for the GeminiSH application.
"""

import subprocess
from input_manager import InputManager
from output_manager import OutputManager

output_manager = OutputManager()
input_manager = InputManager()


def bash(command: str, sensitive: bool = False, user_should_see_output: bool = False):
    """
    Execute a bash command in the user's terminal and return the result.
    With these commands, you can access the local file system.
    Do not use this function to edit text files.

    Parameters:
    command (str): The command to be executed.
    sensitive (bool): If True, the command is considered sensitive and it will 
                      automatically ask for confirmation. Explain to the user 
                      what the command does before executing it.
    user_should_see_output (bool): If True, the user will see the output of the command.

    Returns:
    str: The result of the command or an error message.
    """
    if not command or not command.strip():
        return "[error]Empty command provided[/error]"

    if sensitive:
        output_manager.print(
            f"[yellow]The command [bold]{command}[/bold] is sensitive. "
            "Do you want to execute it? (y/n): [/yellow]"
        )
        confirmation = input_manager.input()
        if confirmation.lower() not in ["y", "yes"]:
            output_manager.print(
                "[yellow italic]Command execution [bold]cancelled[/bold][/yellow italic]"
            )
            return "[error]Command execution cancelled by user[/error]"

    try:
        result = subprocess.check_output(command, shell=True, text=True)
        if user_should_see_output:
            output_manager.print(f"[italic]{result.strip()}[/italic]")
        else:
            return f"[result]{result.strip()}[/result]"
    except subprocess.CalledProcessError as e:
        return f"[error]{e.output}[/error]"
    except Exception as e:
        output_manager.print(e)
        return f"[error]{str(e)}[/error]"
