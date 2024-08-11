import os
import uuid
import json

from datetime import datetime
from google.protobuf.struct_pb2 import Struct
from google.ai.generativelanguage import FunctionCall, FunctionResponse, Content, Part, FileData

FIRST_RUN_THRESHOLD = int(os.getenv("FIRST_RUN_THRESHOLD", 3))

class ChatManager:
    HISTORY_FILE_NAME = "history.json"
    
    def __init__(self, config_manager, output_manager, input_manager, state_manager):
        self.config_manager = config_manager
        self.output_manager = output_manager
        self.input_manager = input_manager
        self.state_manager = state_manager
        
        self.chat_history = self.check_chat_history()
        self.chat_id = str(uuid.uuid4())
        self.current_chat = []

    def check_chat_history(self):
        """Carga el historial de chat desde el archivo history.json."""
        history_file = os.path.join(self.config_manager.directory, self.HISTORY_FILE_NAME)
        if os.path.exists(history_file):
            with open(history_file, "r") as f:
                try:
                    chat_history = json.load(f)
                except json.JSONDecodeError:
                    chat_history = {}
                if not self.config_manager.is_agent and len(chat_history.keys()) <= FIRST_RUN_THRESHOLD:
                    self.state_manager.set_first_run(True)
                return chat_history
        else:
            with open(history_file, "w") as f:
                json.dump({}, f, indent=4)
            if not self.config_manager.is_agent:
                self.state_manager.set_first_run(True)
            return {}

    def create_chat(self):
        """Crea un nuevo chat."""
        self.chat_history[self.chat_id] = {
            "turns": [],
            "created_at": datetime.now().isoformat()
        }

    def save_chat_history(self):
        """Guarda el historial de chat en el archivo history.json."""
        if self.config_manager.is_agent:
            history_file = os.path.join(self.config_manager.agent_directory, self.HISTORY_FILE_NAME)
        else:
            history_file = os.path.join(self.config_manager.directory, self.HISTORY_FILE_NAME)
        with open(history_file, "w") as f:
            json.dump(self.chat_history, f, indent=4)

    def add_part(self, part, proto_part, role, save=True):
        """Adds a new part to the chat history."""
        if self.chat_history and self.chat_id in self.chat_history:
            last_turns = self.chat_history[self.chat_id]["turns"]
            if last_turns and last_turns[-1] and last_turns[-1]["role"] == role:
                # Check if the last part has the same role and merge parts
                self.current_chat[-1].parts.append(proto_part)
                last_turns[-1]["parts"].append(part)
            else:
                self.current_chat.append(Content(parts=[proto_part], role=role))
                last_turns.append({"role": role, "parts": [part]})
        else:
            self.create_chat()
            self.chat_history[self.chat_id]["turns"].append({"role": role, "parts": [part]})
            self.current_chat.append(Content(parts=[proto_part], role=role))
        if save:
            self.save_chat_history()

    def add_text_part(self, role, text, save=True):
        """Adds a new user message to the chat history."""
        part = {"text": text}
        proto_part = Part(text=text)
        self.add_part(part, proto_part, role, save)

    def add_function_call(self, role, function_name, function_args, save=True):
        """Adds a new function call to the chat history."""
        part = {"function_call": {"name": function_name, "args": function_args}}
        proto_part = Part(function_call=FunctionCall(name=function_name, args=function_args))
        self.add_part(part, proto_part, role, save)
        
    def add_function_response(self, role, function_name, function_response, save=True):
        """Adds a new function response to the chat history."""
        part = {"function_response": {"name": function_name, "response": function_response}}
        proto_struct_response = Struct()
        proto_struct_response.update({"response": function_response})
        proto_part = Part(function_response=FunctionResponse(name=function_name, response=proto_struct_response))
        self.add_part(part, proto_part, role, save)

    def add_file(self, file, save=True):
        """Adds a new file to the chat history."""
        proto_part = Part(file_data=FileData(mime_type=file['mime_type'], file_uri=file['uri']))
        self.add_part(file, proto_part, "user", save)
        
    def load_chat(self, chat_id):
        """Loads a chat from history and creates the current_chat with corresponding protos."""
        if chat_id in self.chat_history:
            self.chat_id = chat_id
            self.current_chat = []
            for turn in self.chat_history[chat_id]["turns"]:
                role = turn["role"]
                for part in turn["parts"]:
                    if "text" in part:
                        self.add_text_part(role, part["text"], save=False)
                    elif "function_call" in part:
                        self.add_function_call(role, part["function_call"]["name"], part["function_call"]["args"], save=False)
                    elif "function_response" in part:
                        self.add_function_response(role, part["function_response"]["name"], part["function_response"]["response"], save=False)
        else:
            self.output_manager.error(f"Chat ID {chat_id} not found in history.")