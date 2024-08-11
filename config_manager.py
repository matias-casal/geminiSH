
import os
import json
import platform

class ConfigManager:
    DEFAULT_DIR = ".geminiSH"
    CONFIG_FILE = "config.json"
    
    def __init__(self):
        self.default_directory = self.get_directory()
        self.config = self.load_config(os.path.join(self.default_directory, self.CONFIG_FILE), True) or {}
        self.agent_directory = self.get_agent_directory()
        self.directory = self.default_directory
        self.is_agent = False
        
        if self.default_directory != self.agent_directory:
            self.config_agent = self.load_config(os.path.join(self.agent_directory, self.CONFIG_FILE))
            if self.config_agent:
                self.is_agent = True
                self.directory = self.agent_directory
                self.config.update(self.config_agent)
        
    def load_config(self, file_path, raise_error=False):
        """Carga la configuración principal desde el archivo config.json."""
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                return json.load(f)
        elif raise_error:
            raise FileNotFoundError(f"El archivo de configuración: {file_path} no se encontró y por lo tanto no se puede continuar")
        else:
            return None

    def get_directory(self):
        """Devuelve la ruta del directorio donde se encuentra el programa."""
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), self.DEFAULT_DIR)

    def get_agent_directory(self):
        """Devuelve la ruta del directorio del agente."""
        return os.path.join(os.getcwd(), self.config.get("AGENT_DIR", self.DEFAULT_DIR))

    
    def get_system_information(self):
        """Devuelve la información del sistema."""
        datos_sistema = {
            "system_name": os.uname().sysname,
            "system_version": os.uname().version,
            "system_architecture": os.uname().machine,
            "platform": platform.system(),              
            "platform_release": platform.release(),     
            "platform_version": platform.version(),     
            "platform_machine": platform.machine(),     
            "platform_processor": platform.processor(), 
            "python_version": platform.python_version(),
            "python_build": platform.python_build(),    
            "node_name": platform.node(),               
            "system_uname": platform.uname(),           
        }
        return "\n".join([f"{key}: {value}" for key, value in datos_sistema.items()])
