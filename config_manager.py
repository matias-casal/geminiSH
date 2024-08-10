# config_manager.py

from email.policy import default
import json
import os

class ConfigManager:
    DEFAULT_DIR = ".geminiSH"
    CONFIG_FILE = "config.json"
    
    def __init__(self, input_manager, output_manager):
        self.input_manager = input_manager
        self.output_manager = output_manager
        self.default_directory = self.get_directory()
        self.config = self.load_config(os.path.join(self.default_directory, self.CONFIG_FILE), True)
        self.agent_directory = self.get_agent_directory(self.config["AGENT_DIR"])
        self.directory = self.default_directory
        self.is_agent = False
        
        if self.default_directory != self.agent_directory:
            self.config_agent = self.load_config(os.path.join(self.agent_directory, self.CONFIG_FILE))
            if self.config_agent:
                self.is_agent = True
                self.directory = self.agent_directory
                self.config = self.config.update(self.config_agent)
        
    def load_config(self, file_path, raise_error=False):
        """Carga la configuración principal desde el archivo config.json."""
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                return json.load(f)
        elif raise_error:
            raise FileNotFoundError(f"El archivo de configuración: {file_path} no se encontró y por lo tanto no se puede continuar")
        else:
            return False

    def get_directory(self):
        """Devuelve la ruta del directorio donde se encuentra el programa."""
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), self.DEFAULT_DIR)

    def get_agent_directory(self, default_agent_directory):
        """Devuelve la ruta del directorio del agente."""
        return os.path.join(os.getcwd(), default_agent_directory)
    
    def get_api_key(self):
        """Checks if the GOOGLE_API_KEY is set, if not, prompts the user to enter it."""
        if self.config["GOOGLE_API_KEY"]:
            api_key = config["GOOGLE_API_KEY"]
        elif os.environ.get("GOOGLE_API_KEY"):
            api_key = os.environ["GOOGLE_API_KEY"]
        else:
            self.output_manager.print(
                "API Key is not set. Please visit https://aistudio.google.com/app/apikey to obtain your API key.",
                style="bold red",
            )
            api_key = self.input_manager.input("Enter your GOOGLE_API_KEY: ")
        self.config["GOOGLE_API_KEY"] = api_key
        return api_key