import os
import importlib
import inspect
from pathlib import Path
from time import sleep
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
        """Carga las funciones desde la carpeta functions."""
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
                        spec = importlib.util.spec_from_file_location(module_name, module_path)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)

                        for func_name, func in module.__dict__.items():
                            if callable(func) and not func_name.startswith("__") and not inspect.isclass(func):
                                functions[func_name] = func
                    except Exception as e:
                        self.output_manager.debug(f"Error loading function from '{filename}': {e}")
        
        if not functions and not is_agent:
            self.output_manager.debug(f'functions_directory: {functions_directory}')
            self.output_manager.warning("No se encontraron funciones en el modo default, lo cual no es normal. Gemini se ejecutara sin sus funciones basicas.")

        return functions

    def set_model_manager(self, model_manager):
        """Establece el model_manager después de la inicialización."""
        self.model_manager = model_manager
        
    def get_as_declarations(self):
        """Convierte las funciones en declaraciones de función."""
        return [self._create_function_declaration(func) for func in self.functions.values()]

    def _create_function_declaration(self, func):
        """Crea una declaración de función a partir de una función de Python."""
        func_name = func.__name__
        func_doc = func.__doc__.strip() if func.__doc__ else "No description provided."
        func_signature = inspect.signature(func)
        properties = {}
        required = []
        for param_name, param in func_signature.parameters.items():
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
            )
        )

    def _convert_python_type_to_proto_type(self, python_type):
        """Convierte un tipo de Python a un tipo proto correspondiente."""
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
        elif actual_type == dict:
            return Schema(type_=Type.OBJECT)
        else:
            return Schema(type_=Type.STRING)

    def execute_function(self, function_name, args):
        """Ejecuta una función con los argumentos proporcionados."""
        if function_name in self.functions:
            try:
                return self.functions[function_name](**args)
            except Exception as e:
                return f"[error]Error executing function: {e}[/error]"
        else:
            return f"[error]Function not found: {function_name}[/error]"
        
    def handle_agent_functions_response(self, response):
        """Maneja la respuesta de una función del agente."""
        if isinstance(response, dict):
            if 'files_to_upload' in response:
                file_paths = response['files_to_upload']
                upload_response = self.functions['upload_files'](file_paths)
                for file in upload_response['response_to_agent']['files']:
                    self.chat_manager.add_file(file)
            elif 'files' in response:
                for file in response['files']:
                    self.chat_manager.add_file(file)
            elif 'require_execution_result' in response:
                self.model_manager.generate_content()
            elif 'load_chat_history' in response:
                self.functions['load_chat_history'](response['load_chat_history'])
            