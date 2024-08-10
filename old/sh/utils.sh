# Function to display help message
display_help() {
  echo "Usage: gemini.sh [QUERY | install]"
  echo "  QUERY: Your query for Gemini"
  echo "  install: Install the Python version of this tool"
}

# Function to get the API key
get_api_key() {
  if [[ -z "${GOOGLE_API_KEY+x}" ]]; then
    read -r -p "Enter your GOOGLE_API_KEY: " api_key
    echo "${api_key}"
  else
    echo "${GOOGLE_API_KEY}"
  fi
}

# Function to prepare and send the chat request to Gemini
send_chat_request() {
  local user_input="${1}"
  local api_key="${2}"
  local request_body

  # Construct the JSON request body
  request_body=$(cat <<EOF
{
  "prompt": {
    "messages": [
      {"content": "${user_input}"}
    ]
  }
}
EOF
)

  # Use curl to send the request
  curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateMessage?key=${api_key}" \
    -H 'Content-Type: application/json' \
    -X POST \
    -d "${request_body}" > response.json
}

# Function to get and display the chat response
get_chat_response() {
  local response_text
  echo $response_text
  # Extract the response text using grep and sed
  response_text=$(grep -o '"content": "[^"]*"' response.json | sed 's/"content": "//g' | sed 's/"//g')

  # Display the response
  echo "Gemini: ${response_text}"

  # Remove the response file
  rm response.json
}