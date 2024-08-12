import os
import importlib
import inspect
import subprocess
import sys
import re

from google.ai.generativelanguage import FunctionDeclaration, Schema, Type

class FunctionManager:
    def __init__(self, config_manager, chat_manager, output_manager, input_manager):
        self.config_manager = config_manager
        self.chat_manager = chat_manager
        self.output_manager = output_manager
        self.input_manager = input_manager
        self.functions = self.load_functions()
        if self.config_manager.is_agent:
            agent_functions = self.load_functions(True)
            self.functions.update(agent_functions)
            
    def load_functions(self, is_agent=False):
        """Load functions from the functions folder and check dependencies."""
        functions = {}
        if is_agent:
            functions_directory = os.path.join(self.config_manager.get_agent_directory(), "functions")
        else:
            functions_directory = os.path.join(self.config_manager.get_directory(), "functions")
        if not os.path.exists(functions_directory):
            os.makedirs(functions_directory)
        else:
            for filename in os.listdir(functions_directory):
                if filename.endswith(".py"):
                    try:
                        module_name = filename[:-3]
                        module_path = os.path.join(functions_directory, filename)
                        # Check and install missing dependencies
                        try:
                            self._check_and_install_dependencies(module_path)
                        except Exception as e:
                            self.output_manager.debug(f"Error checking and installing dependencies for '{filename}': {e}")

                        spec = importlib.util.spec_from_file_location(module_name, module_path)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)  # Ensure the module is executed
                        for func_name, func in module.__dict__.items():
                            if callable(func) and not func_name.startswith("__") and not inspect.isclass(func):
                                functions[func_name] = func
                    except Exception as e:
                        self.output_manager.debug(f"Error loading function from '{filename}': {e}")
        
        if not functions and not is_agent:
            self.output_manager.debug(f'functions_directory: {functions_directory}')
            self.output_manager.warning("No functions found in default mode, which is not normal. Gemini will run without its basic functions.")

        return functions
    
    def _check_and_install_dependencies(self, module_path):
        """Check and install necessary dependencies for a module."""
        with open(module_path, "r") as file:
            content = file.read()
        
        # Find all import statements
        imports = re.findall(r'^\s*(?:import|from)\s+([a-zA-Z0-9_\.]+)', content, re.MULTILINE)
        
        for package in imports:
            try:
                importlib.import_module(package.split('.')[0])
            except ImportError:
                self.output_manager.debug(f"Installing missing package: {package}")
                subprocess.check_call([sys.executable, "-m", "pip", "install", package.split('.')[0]], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
    def set_model_manager(self, model_manager):
        """Set the model_manager after initialization."""
        self.model_manager = model_manager
        
    def get_as_declarations(self):
        """Convert functions into function declarations."""
        return [self._create_function_declaration(func) for func in self.functions.values()]

    def _create_function_declaration(self, func):
        """Create a function declaration from a Python function."""
        func_name = func.__name__
        func_doc = func.__doc__.strip() if func.__doc__ else "No description provided."
        func_signature = inspect.signature(func)
        properties = {}
        required = []
        params_items = func_signature.parameters.items()
        for param_name, param in params_items:
            param_type = self._convert_python_type_to_proto_type(param.annotation)
            properties[param_name] = param_type
            if param.default == inspect._empty:
                required.append(param_name)
        
        return FunctionDeclaration(
            name=func_name,
            description=func_doc,
            parameters=Schema(
                type_=Type.OBJECT,
                properties=properties,
                required=required
            ) if params_items else None
        )

    def _convert_python_type_to_proto_type(self, python_type):
        """Convert a Python type to a corresponding proto type."""
        actual_type = python_type[1] if isinstance(python_type, tuple) else python_type
        if actual_type == str:
            return Schema(type_=Type.STRING)
        elif actual_type == int:
            return Schema(type_=Type.INTEGER)
        elif actual_type == float:
            return Schema(type_=Type.NUMBER)
        elif actual_type == bool:
            return Schema(type_=Type.BOOLEAN)
        elif isinstance(actual_type, list):
            item_type = self._convert_python_type_to_proto_type(actual_type[0])
            return Schema(type=Type.ARRAY, items=item_type)
        elif isinstance(actual_type, dict):
            return Schema(type_=Type.OBJECT)
        else:
            return Schema(type_=Type.STRING)

    def execute_function(self, function_name, args):
        """Execute a function with the provided arguments."""
        if function_name in self.functions:
            try:
                return self.functions[function_name](**args)
            except Exception as e:
                return f"[error]Error executing function: {e}[/error]"
        else:
            return f"[error]Function not found: {function_name}[/error]"
        
    def handle_functions_response(self, response):
        """Handles the response of a function."""
        if isinstance(response, dict):
            if 'files_to_upload' in response:
                file_paths = response['files_to_upload']
                upload_response = self.functions['upload_files'](file_paths)
                for file in upload_response['response_to_agent']['files']:
                    self.chat_manager.add_file(file)
            if 'files' in response:
                for file in response['files']:
                    self.chat_manager.add_file(file)
            if 'load_chat_history' in response:
                self.chat_manager.load_chat(response['load_chat_history'])
