from prompt_toolkit import PromptSession, HTML
from rich.console import Console

console = Console()
session = PromptSession()

def finished_ask(task_description: str) -> str:
    """
    Ask the user for feedback to continue if the previous task is determined to be finished.

    Parameters:
    task_description (str): A description of the task that was completed.

    Returns:
    str: A formatted string containing the task description and the user's feedback.
    """
    console.print(f"Task '{task_description}' has been completed.", style="bold green")
    feedback_question = "Do you want to provide feedback before continuing? (yes/no)"
    feedback = session.prompt(HTML(f"<ansiyellow>{feedback_question}</ansiyellow> "))
    
    if feedback.lower() in ['yes', 'y']:
        user_feedback = session.prompt(HTML("<ansiyellow>Please provide your feedback:</ansiyellow> "))
        return f"[task]{task_description}[/task][feedback]{user_feedback}[/feedback]"
    else:
        return f"[task]{task_description}[/task][feedback]No feedback provided[/feedback]"