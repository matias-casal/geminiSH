import inspect
from rich.console import Console
from rich.markdown import Markdown

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
        caller_info = f"{caller_frame.function} at line {caller_frame.lineno} in {caller_frame.filename.split('/')[-1]}"
        if level == 1:
            self.console.print(f"[yellow][bold]DEBUG:[/bold] {text}[/yellow] [italic][blue]({caller_info})[/blue][/italic]")
        elif level == 2:
            self.console.print(f"[yellow][bold italic]DEBUG:[/bold italic] {text}[/yellow] [italic][blue]({caller_info})[/blue][/italic]")
            
    def warning(self, text):
        """Imprime texto en la consola como un warning."""
        self.console.print(f"[yellow][bold]WARNING:[/bold] {text}[/yellow]")