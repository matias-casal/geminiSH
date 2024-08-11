import os
import inspect
from rich.console import Console
from rich.markdown import Markdown

DEBUG = int(os.getenv("DEBUG", 0))

class OutputManager:
    def __init__(self): 
        self.console = Console()

    def print(self, text, markdown=False, style=""):
        """Imprime texto en la consola."""
        if not text:
            return
        if markdown:
            self.console.print(Markdown(text, style=style)) # type: ignore
        else:
            self.console.print(text, style=style)
            
    def debug(self, text, level=1):
        """Imprime texto en la consola segun el nivel de debug."""
        caller_frame = inspect.stack()[1]
        caller_info = f"{caller_frame.function} in {caller_frame.filename.split('/')[-1]}:{caller_frame.lineno}"
        if DEBUG:
            if level == 1 and DEBUG:
                self.print(f"[yellow][bold]DEBUG:[/bold] {text}[/yellow]\n[italic][blue]({caller_info})[/blue][/italic]")
            if level >= 2 and DEBUG >= 2:
                self.print(f"[yellow][bold italic]DEBUG:[/bold italic] {text}[/yellow]\n[italic][blue]({caller_info})[/blue][/italic]")
            if level >= 3 and DEBUG == 3:
                self.print(f"[red][bold italic]DEBUG:[/bold italic][/red]")
            
    def warning(self, text):
        """Imprime texto en la consola como un warning."""
        self.console.print(f"[yellow][bold]WARNING:[/bold] {text}[/yellow]")