"""
This module manages the input operations for the GeminiSH application.
It handles user input, including command history and auto-suggestions.
"""

from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.shortcuts import CompleteStyle
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from rich.prompt import Prompt


class InputManager:
    """
    The InputManager class handles user input operations for the GeminiSH application.
    It manages command history, auto-suggestions, and key bindings for an enhanced user
    experience. The class is designed as a singleton to ensure consistent input handling
    across the application.
    """
    
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, output_manager=None):
        if not hasattr(self, "initialized"):
            self.output_manager = output_manager
            self.history = InMemoryHistory()

            # Define key bindings
            kb = KeyBindings()

            # Bind Tab key to autocomplete
            @kb.add(Keys.Tab)
            def _(event):
                b = event.current_buffer
                suggestion = b.suggestion
                if suggestion:
                    b.insert_text(suggestion.text)

            # Create session with new key bindings
            self.session = PromptSession(
                history=self.history,
                auto_suggest=AutoSuggestFromHistory(),
                complete_style=CompleteStyle.READLINE_LIKE,
                key_bindings=kb,
            )
            self.initialized = True

    def input(self, message="[bold green]> [/bold green]"):
        """Read a message from the user."""
        if self.output_manager:
            with self.output_manager.stop_status():
                self.output_manager.print(message, end="")
                return self.session.prompt()

    def choose(self, text, choices, default=None):
        """Print text to console and wait for user response."""
        if self.output_manager:
            with self.output_manager.stop_status():
                return Prompt.ask(f"[yellow]{text}[/yellow]", choices=choices, default=default)
