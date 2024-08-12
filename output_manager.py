import os
import inspect
from contextlib import contextmanager
from rich.console import Console
from rich.markdown import Markdown

DEBUG = 1 if os.getenv("DEBUG", "False") == "True" else 0

class OutputManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_manager=None): 
        if not hasattr(self, 'initialized'):  # Ensure __init__ is only called once
            self.console = Console()
            self._status_stack = []
            self.initialized = True
            self.config_manager = config_manager
            
    def print(self, text, markdown=False, style="", end="\n"):
        """Prints text to the console."""
        if not text:
            return
        if markdown:
            self.console.print(Markdown(text, style=style)) 
        else:
            self.console.print(text, end=end)
                
    def debug(self, text, level=1):
        """Prints text to the console according to the debug level."""
        caller_frame = inspect.stack()[1]
        caller_info = f"{caller_frame.function} in {caller_frame.filename.split('/')[-1]}:{caller_frame.lineno}"
        if DEBUG:
            if level == 1 and DEBUG:
                self.print(f"[yellow][bold]DEBUG:[/bold] {text}[/yellow]\n[italic][blue]({caller_info})[/blue][/italic]")
            if level >= 2 and DEBUG >= 2:
                self.print(f"[yellow][bold italic]DEBUG:[/bold italic] {text}[/yellow]\n[italic][blue]({caller_info})[/blue][/italic]")
            if level >= 3 and DEBUG == 3:
                self.print(f"[red][bold italic]DEBUG:[/bold italic] {text}[/red]\n[italic][blue]({caller_info})[/blue][/italic]")
            
    def warning(self, text):
        """Prints text to the console as a warning."""
        self.console.print(f"[yellow][bold]WARNING:[/bold] {text}[/yellow]")

    @contextmanager
    def managed_status(self, message):
        """
        Context manager to handle nested console statuses.
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
        Stops the current status, performs an action, and restarts the status.
        """
        if self._status_stack:
            self._status_stack[-1].stop()

        try:
            yield
        finally:
            if self._status_stack:
                self._status_stack[-1].start()