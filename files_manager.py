import os

class FilesManager:
    def __init__(self, config_manager, output_manager):
        self.config_manager = config_manager
        self.output_manager = output_manager

    def upload_file(self, file_path):
        """Sube un archivo a Gemini."""
        # Implementar la lógica para subir archivos a Gemini
        # ...
        pass

    def read_file(self, file_path):
        """Lee el contenido de un archivo."""
        with open(file_path, "r") as f:
            return f.read()

    def write_file(self, file_path, content):
        """Escribe contenido en un archivo."""
        with open(file_path, "w") as f:
            f.write(content)