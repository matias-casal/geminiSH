"""
This module provides functionality to make a coffee request.
"""
import os
from output_manager import OutputManager

output_manager = OutputManager()

def make_coffee():
    """
    This function is executed when the user requests a coffee.
    It's a joke function that prints a coffee ASCII art in the user's terminal.
    Do not respond with any ASCII art after executing this function.
    """
    file_path_coffee_instructions = os.path.join(
        os.path.dirname(__file__), "../others/coffee_ascii.txt"
    )
    if os.path.exists(file_path_coffee_instructions):
        with open(file_path_coffee_instructions, "r", encoding="utf-8") as file:
            content = file.read()
            output_manager.print(f"[bold bright_yellow]{content}[/bold bright_yellow]")
    else:
        return "[error]The coffee instructions file does not exist.[/error]"
