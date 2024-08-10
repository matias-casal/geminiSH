class InputManager:
    def __init__(self, output_manager):
        self.output_manager = output_manager

    def input(self, message="> "):
        """Lee un mensaje del usuario."""
        return input(message)

    def record_voice(self):
        """Graba la voz del usuario."""
        # Implementar la lógica para grabar la voz del usuario
        # ...
        pass

    def get_clipboard(self):
        """Obtiene el contenido del portapapeles del usuario."""
        # Implementar la lógica para obtener el contenido del portapapeles
        # ...
        pass