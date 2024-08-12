"""
This module provides functionality to load chat history for the GeminiSH application.
"""

import os
import json
from datetime import datetime
from output_manager import OutputManager
from input_manager import InputManager

output_manager = OutputManager()
input_manager = InputManager()


def load_chat_history(
    chat_id=None, load_nth_last=None, return_all=False
):
    """
    Load chat history from history.json.

    Args:
        chat_id (str, optional): The ID of the chat to load.
        load_nth_last (int, optional): Load the nth last chat.
        return_all (bool, optional): If True, return all history.

    Returns:
        str: The chat id or an error message.
    """
    try:
        history_file = os.path.join(
            output_manager.config_manager.directory, "history.json"
        )
        if not os.path.exists(history_file):
            return f"[error]File {history_file} not found.[/error]"

        with open(history_file, "r", encoding="utf-8") as file:
            history_data = json.load(file)

        if return_all:
            try:
                return {
                    "response": json.dumps(history_data, indent=0),
                    "response_to_agent": {"require_execution_result": True},
                }
            except Exception:
                return "[error]Error loading history.[/error]"

        if load_nth_last is not None:
            try:
                nth_last_chat_id = list(history_data.keys())[
                    -load_nth_last
                ]
                return {
                    "response_to_agent": {"load_chat_history": nth_last_chat_id}
                }
            except IndexError:
                return f"[error]Not enough chats to load the " \
                       f"{load_nth_last}th last chat.[/error]"

        if not chat_id:
            chat_list = []
            for cid, chat in history_data.items():
                first_text = chat["turns"][0]["parts"][0]["text"][:50] + "..."
                created_at = datetime.fromisoformat(
                    chat["created_at"]
                ).strftime("%Y-%m-%d %H:%M:%S")
                chat_list.append(
                    {
                        "chat_id": cid,
                        "preview": first_text,
                        "created_at": created_at,
                    }
                )

            output_manager.print(
                "\n\n# Available Chats", style="bold magenta", markdown=True
            )
            for index, chat in enumerate(chat_list, start=1):
                output_manager.print(
                    f"{index}. {chat['preview']} "
                    f"(Created at: {chat['created_at']})",
                    style="bold blue",
                )

            output_manager.print(
                f"{len(chat_list) + 1}. Exit", style="bold blue"
            )

            choices = [str(i) for i in range(1, len(chat_list) + 2)]
            choice = input_manager.choose("Choose a chat ID:", choices)
            if int(choice) <= len(chat_list):
                chat = chat_list[int(choice) - 1]
                chat_id = chat["chat_id"]
            else:
                return "[error]Exiting chat selection.[/error]"

        if chat_id in history_data:
            return {"response_to_agent": {"load_chat_history": chat_id}}
        else:
            return f"[error]Chat ID {chat_id} not found.[/error]"
    except Exception as e:
        output_manager.print(e)
        return f"[error]Error loading history: {e}[/error]"
    