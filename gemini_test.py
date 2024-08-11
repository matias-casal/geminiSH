import os

class StateManager:
    def __init__(self, config_manager, output_manager):
        self.config_manager = config_manager
        self.output_manager = output_manager
        self.state = {
            "is_first_run": False,
            "system_instructions": ""
        }
        
        self.init_state()

    def init_state(self):
        """Inicializa el estado de la aplicación."""
        # Load the system instructions from the config
        if self.config_manager.is_agent:
            agent_instructions_path = os.path.join(self.config_manager.get_agent_directory(), "prompts", "system_instructions.md")
            if os.path.exists(agent_instructions_path):
                with open(agent_instructions_path, "r") as f:
                    self.state["system_instructions"] = f.read() or " "
                return
        
        default_instructions_path = os.path.join(self.config_manager.get_directory(), "prompts", "system_instructions.md")
        if os.path.exists(default_instructions_path):
            with open(default_instructions_path, "r") as f:
                self.state["system_instructions"] = f.read() or " "
        else:
            self.output_manager.debug(f"System instructions not found in {default_instructions_path}")
            raise Exception("System instructions not found.")

    def is_first_run(self):
        """Verifica si es la primera vez que se ejecuta la aplicación."""
        
        return self.state.get("is_first_run", False)

    def set_first_run(self, is_first_run):
        """Establece el estado de la primera ejecución."""
        self.state["is_first_run"] = is_first_run
        
