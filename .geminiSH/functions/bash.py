import subprocess
from input_manager import InputManager
from output_manager import OutputManager

output_manager = OutputManager()
input_manager = InputManager()

def bash(command: str, sensitive: bool = False, user_should_see_output: bool = False, need_to_analyze_output: bool = False):
    """
    Execute a bash command in the users terminal and return the result.
    With these commands, you can access the local file system.
    For example, you can chain multiple commands together using operators like `&&` or `||`.
    If the command will respond the users request directly, set user_should_see_output to True, if you need to analyze the output, set it to False.
    If you need to analyze the output to give the user a full response, set need_to_analyze_output to True
    Use the system information to craft the right command, for example you can open files to show to the user in a mac with the command `open <file_path>`, or in a linux with `xdg-open <file_path>`.
    
    
    Parameters:
    command (str): The command to be executed.
    sensitive (bool): If True, the command is considered sensitive and it will automatically ask for confirmation. Explain to the user what the command does before executing it.
    user_should_see_output (bool): If True, the user will see the output of the command.
    need_to_analyze_output (bool): If True, the output will be sended to you to analyze.
    
    Returns:
    str: The result of the command or an error message.
    """
    if not command or not command.strip():
        return "[error]Empty command provided[/error]"
    
    if sensitive:
        output_manager.print(f"[yellow]The command [bold]{command}[/bold] is sensitive. Do you want to execute it? (y/n): [/yellow]")
        confirmation = input_manager.input()
        if confirmation.lower() not in ['y', 'yes']:
            output_manager.print("[yellow italic]Command execution [bold]cancelled[/bold][/yellow italic]")
            return "[error]Command execution cancelled by user[/error]"
    
    try:
        result = subprocess.check_output(command, shell=True, text=True)
        if user_should_see_output:
            output_manager.print(f"[italic]{result.strip()}[/italic]")
        if need_to_analyze_output:
            return {"response": result.strip(), "response_to_agent": {"require_execution_result": True}}
        else:
            return f"[result]{result.strip()}[/result]"
    except subprocess.CalledProcessError as e:
        return f"[error]{e.output}[/error]"
    except Exception as e:
        output_manager.print(e)
        return f"[error]{str(e)}[/error]"