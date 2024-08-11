
from rich.console import Console

console = Console()

class InputManager:
    def __init__(self, output_manager):
        self.output_manager = output_manager

    def input(self, message="[bold green]> [/bold green]"):
        """Lee un mensaje del usuario."""
        return console.input(message)