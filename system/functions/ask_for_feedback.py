from prompt_toolkit import PromptSession, HTML
from prompt_toolkit.completion import WordCompleter

from rich.console import Console

console = Console()
session = PromptSession()


def ask_the_user(feedback_question: str) -> str:
    """
    Ask the user a question and return their feedback using prompt_toolkit for enhanced interaction.

    Parameters:
    feedback_question (str): The question to be asked to the user.

    Returns:
    str: A formatted string containing the question and the user's feedback.
    """
    feedback = session.prompt(
        HTML(f"<ansiyellow>{feedback_question}</ansiyellow> "))
    return f"[question]{feedback_question}[/question][answer]{feedback}[/answer]"


def chose_options(question: str, options: list[int]) -> str:
    """
    Make the user choose one of the options in the list using prompt_toolkit.

    Parameters:
    question (str): List all the options with their number, like this: question: '1. Option 1\n2. Option 2\n3. Option 3'. If you are going to show the question in your text response, then leave the question empty.
    options (list[int]): The list of numbers relative to the options to be chosen from, like this: [1, 2, 3].

    Returns:
    str: A formatted string containing the question, the options, and the user's choice.
    """
    options_completer = WordCompleter(
        [str(option) for option in options], ignore_case=True)
    choice = session.prompt(
        HTML(f"<ansiyellow>{question}</ansiyellow>\n"), completer=options_completer)
    return f"[question]{question}[/question][options]{options}[/options][choice]{choice}[/choice]"