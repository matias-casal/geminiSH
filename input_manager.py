from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.shortcuts import CompleteStyle
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from rich.prompt import Prompt

class InputManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)  
        return cls._instance

    def __init__(self, output_manager=None):
        if not hasattr(self, 'initialized'): 
            self.output_manager = output_manager
            self.history = InMemoryHistory()
            
            # Definir las asociaciones de teclas
            kb = KeyBindings()

            # Asociar la tecla Tab al autocompletado
            @kb.add(Keys.Tab)
            def _(event):
                b = event.current_buffer
                suggestion = b.suggestion
                if suggestion:
                    b.insert_text(suggestion.text)

            # Crear la sesión con las nuevas asociaciones de teclas
            self.session = PromptSession(
                history=self.history,
                auto_suggest=AutoSuggestFromHistory(),
                complete_style=CompleteStyle.READLINE_LIKE,
                key_bindings=kb,
            )
            self.initialized = True

    def input(self, message="[bold green]> [/bold green]"):
        """Read a message from the user."""
        with self.output_manager.stop_status():
            self.output_manager.print(message, end="")
            return self.session.prompt()
        
    def choose(self, text, choices, default=None):
        """Imprime texto en la consola y espera una respuesta del usuario."""
        with self.output_manager.stop_status():
            return Prompt.ask(f"[yellow]{text}[/yellow]", choices=choices, default=default)