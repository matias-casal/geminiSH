import subprocess


def bash(command: str) -> str:
    """
    Execute a command in the same shell that the agent is running and return the result. Take into consideration that the command is a bash command. 
    With these commands, you can access the local file system, so you can create the inline command you want, grouping everything you need. 
    For example, you can list files in a directory, create new files, delete files, or even chain multiple commands together using operators like `&&` or `||`.
    # With this command execution function, it can access all files that the user asks for. If the provided command includes a file path, it can access, read, modify, or delete the file at that path. This allows for extensive file system operations, including listing directory contents, creating new files, deleting files, and chaining multiple commands together.
    
    Parameters:
    command (str): The command to be executed.

    Returns:
    str: A formatted string containing the command and its result or an error message.
    """
    try:
        result = subprocess.check_output(command, shell=True, text=True)
        print(f'\n\n +-+-=-+-+ Result: {result}\n\n')
        return f"[result]{result.strip()}[/result]"
    except subprocess.CalledProcessError as e:
        return f"[error]{str(e)}[/error]"

