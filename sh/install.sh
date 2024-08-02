#!/bin/bash

# The repository URL
repo_url="https://github.com/matias-casal/geminiSH.git"

echo "Installing Python and Git..."

# Check OS and install Python and Git accordingly
if [[ "$(uname -s)" == "Darwin" ]]; then
    # Install Python and Git using Homebrew on macOS
    brew install python git
elif [[ "$(uname -s)" == "Linux" ]]; then
    # Install Python and Git using the package manager on Linux (Debian/Ubuntu)
    sudo apt-get update
    sudo apt-get install -y python3 git
elif [[ "${OSTYPE}" == "msys" || "${OSTYPE}" == "cygwin" ]]; then
    # Check if Chocolatey is installed
    if ! command -v choco &> /dev/null; then
        echo "Chocolatey is not installed. Installing now..."

        # Install Chocolatey (requires administrative privileges)
        @"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command "iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))" && SET "PATH=%PATH%;%ALLUSERSPROFILE%\chocolatey\bin"
        echo "Chocolatey installed successfully."
    fi

    # Install Python and Git using Chocolatey
    choco install python3 git
else
    echo "Unsupported operating system. Please install Python and Git manually."
    exit 1
fi

echo "Python and Git installed successfully."

# Clone the repository
echo "Cloning repository from ${repo_url}..."
git clone "${repo_url}" geminiSH

echo "Repository cloned successfully."

# Navigate to the repository directory
cd geminiSH

# Install the required Python packages
echo "Installing Python requirements..."
python3 -m pip install -r requirements.txt

echo "Python requirements installed successfully."

# Create the geminiSH alias depending on the OS
if [[ "$(uname -s)" == "Darwin" || "$(uname -s)" == "Linux" ]]; then
    echo "alias geminiSH='python3 main.py'" >> ~/.bashrc
    source ~/.bashrc
elif [[ "${OSTYPE}" == "msys" || "${OSTYPE}" == "cygwin" ]]; then
    echo "doskey geminiSH=python3 main.py \"\$*\"" >> ~/.bashrc
    source ~/.bashrc
else
    echo "Unsupported operating system. Please create the alias manually: 'alias geminiSH='python3 main.py''"
fi

echo "Alias 'geminiSH' created successfully. You can now use 'geminiSH' to interact with Gemini."