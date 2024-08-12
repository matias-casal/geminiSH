"""
This module manages the output operations for the GeminiSH application.
"""

import os
import inspect
from contextlib import contextmanager
from rich.console import Console
from rich.markdown import Markdown

DEBUG = 1 if os.getenv("DEBUG", "False") == "True" else 0


class OutputManager:
    """
    Manages output to the console, including printing, debugging, warnings, and status messages.
    This class is designed as a singleton to ensure consistent output handling.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_manager=None):
        if not hasattr(self, "initialized"):  # Ensure __init__ is only called once
            self.console = Console()
            self._status_stack = []
            self.initialized = True
            self.config_manager = config_manager

    def print(self, text, markdown=False, style="", end="\n"):
        """
        Prints text to the console.

        Args:
            text (str): The text to print.
            markdown (bool, optional): Whether to render the text as Markdown. Defaults to False.
            style (str, optional): Rich console style to apply to the text. Defaults to "".
            end (str, optional): String appended after the last value, default a newline.
        """
        if not text:
            return
        if markdown:
            self.console.print(Markdown(text, style=style))
        else:
            self.console.print(text, end=end)

    def debug(self, text, level=1):
        """
        Prints debug messages to the console, controlled by the DEBUG environment variable.

        Args:
            text (str): The debug message to print.
            level (int, optional): The debug level (1, 2, or 3).
        """
        caller_frame = inspect.stack()[1]
        caller_filename = caller_frame.filename.split('/')[-1]
        caller_info = f"{caller_frame.function} in {caller_filename}:{caller_frame.lineno}"
        if DEBUG:
            if level == 1 and DEBUG:
                self.print(
                    f"[yellow][bold]DEBUG:[/bold] {text}[/yellow]\n"
                    f"[italic][blue]({caller_info})[/blue][/italic]"
                )
            if level >= 2 and DEBUG >= 2:
                self.print(
                    f"[yellow][bold italic]DEBUG:[/bold italic] {text}[/yellow]\n"
                    f"[italic][blue]({caller_info})[/blue][/italic]"
                )
            if level >= 3 and DEBUG == 3:
                self.print(
                    f"[red][bold italic]DEBUG:[/bold italic] {text}[/red]\n"
                    f"[italic][blue]({caller_info})[/blue][/italic]"
                )

    def warning(self, text):
        """
        Prints a warning message to the console.

        Args:
            text (str): The warning message to print.
        """
        self.console.print(f"[yellow][bold]WARNING:[/bold] {text}[/yellow]")

    @contextmanager
    def managed_status(self, message):
        """
        Context manager to display a status message in the console.
        Handles nested status messages gracefully.

        Args:
            message (str): The status message to display.
        """
        if self._status_stack:
            self._status_stack[-1].stop()

        status = self.console.status(message)
        self._status_stack.append(status)
        status.start()

        try:
            yield
        finally:
            status.stop()
            self._status_stack.pop()

    @contextmanager
    def stop_status(self):
        """
        Context manager to temporarily stop the current status message,
        execute a block of code, and then restart the status message.
        """
        if self._status_stack:
            self._status_stack[-1].stop()

        try:
            yield
        finally:
            if self._status_stack:
                self._status_stack[-1].start()
