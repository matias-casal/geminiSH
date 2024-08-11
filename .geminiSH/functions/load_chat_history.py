import os
import json
from datetime import datetime
from output_manager import OutputManager
from input_manager import InputManager

output_manager = OutputManager()
input_manager = InputManager()


def load_chat_history(chat_id=None, load_nth_last=None, return_all=False):
    """
    Load chat history from history.json.
    Use this function if the user refers to a previous chat.
    If the user ask you something about your previous conversations, use the return_all parameter.
    In case that the response with return_all is an error, ask the user if it wants to search and choose a chat from a list.

    Args:
        chat_id (str, optional): The ID of the chat to load. If not provided, a list of available chats will be shown.
        load_nth_last (int, optional): If provided, load the nth last chat history (e.g., 1 for last, 2 for second last).
        return_all (bool, optional): If True, return all chat history.
    
    Returns:
        str: The chat id after the user selects one or a error message.
    """

    try:
        # Load history data from history.json
        history_file = os.path.join(output_manager.config_manager.directory, "history.json")
        if not os.path.exists(history_file):
            return f"[error]The file {history_file} does not exist.[/error]"
        
        with open(history_file, 'r') as file:
            history_data = json.load(file)
        
        if return_all:
            # Return all chat history as a JSON string
            try:
                return  {
                    "response": json.dumps(history_data, indent=0),
                    "response_to_agent": { "require_execution_result": True }
                }
            except Exception as e:
                return f"[error]An error occurred while loading the history[/error]"

        if load_nth_last is not None:
            # Load the nth last chat history (considering reversed order)
            try:
                nth_last_chat_id = list(history_data.keys())[load_nth_last - 1]  # Adjusted index for reversed order
                nth_last_chat = history_data[nth_last_chat_id]
                return {
                    "response": nth_last_chat["turns"],
                    "response_to_agent": {"load_chat_history": nth_last_chat_id}
                }
            except IndexError:
                return f"[error]There are not enough chats in the history to load the {load_nth_last}th last chat.[/error]"

        if not chat_id:
            # List available chat histories
            chat_list = []
            for cid, chat in history_data.items():
                first_text = f'{chat["turns"][0]["parts"][0]["text"][:50]}...'
                created_at = datetime.fromisoformat(chat['created_at']).strftime('%Y-%m-%d %H:%M:%S')
                chat_list.append({'chat_id': cid, 'preview': first_text, 'created_at': created_at})
            
            # Display options to the user
            output_manager.print(f"\n\n# Available Chats", style="bold magenta", markdown=True)
            for index, chat in enumerate(chat_list, start=1):
                output_manager.print(f"{index}. {chat['preview']} (Created at: {chat['created_at']})", style="bold blue")
            
            output_manager.print(f"{len(chat_list) + 1}. Exit", style="bold blue")
            
            choices = [str(i) for i in range(1, len(chat_list) + 2)]
            choice = input_manager.choose("Choose a chat ID:", choices)
            chat = chat_list[int(choice) - 1]
            chat_id = chat['chat_id']
        
        # Load the specified chat history
        if chat_id in history_data:
            chat = history_data[chat_id]
            return {
                "response": chat,
                "response_to_agent": {"load_chat_history": chat_id}
            }
        else:
            return f"[error]Chat ID {chat_id} not found in history.[/error]"
    except Exception as e:
        output_manager.print(e)
        return f"[error]An error occurred while loading the history: {e}[/error]"