#!/bin/bash

# Source the utility functions
source sh/utils.sh

# Main logic
if [ $# -eq 0 ]; then
    display_help
elif [ "$1" == "install" ]; then
    sh/install.sh
else
    # Get API Key
    api_key=$(get_api_key)

    # Prepare and send request to Gemini
    user_input="$*"
    send_chat_request "${user_input}" "${api_key}"

    # Get and display response
    get_chat_response
fi