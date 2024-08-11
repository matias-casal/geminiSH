import os
import traceback
from gemini_agent import GeminiAgent

DEBUG = os.environ.get("DEBUG", False)

def main():
    """Main function to handle the execution of the Gemini Agent."""
    agent = GeminiAgent()
    try:
        agent.run()
    except KeyboardInterrupt:
        agent.exit()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt detected. Exiting gracefully.")