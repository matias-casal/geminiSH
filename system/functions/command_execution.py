import subprocess

def command_execution(command: str) -> str:
    f"""
    Execute a command and return the result. Take in consideration that the command is a bash command. 
    This is the data of the machine where the command is executed: 

    Parameters:
    command (str): The command to be executed.

    Returns:
    str: A formatted string containing the command and its result or an error message.
    """
    try:
        result = subprocess.check_output(command, shell=True, text=True)
        return f"[command]{command}[/command][result]{result.strip()}[/result]"
    except subprocess.CalledProcessError as e:
        return f"[command]{command}[/command][error]{e.stderr.strip()}[/error]"
