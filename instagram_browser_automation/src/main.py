# This file will be the main entry point for the application.
# It will coordinate the browser controller and the Gemini analyzer.

import argparse
import time
from browser_controller import BrowserController # Assuming it's in the same directory or PYTHONPATH is set
from gemini_analyzer import GeminiAnalyzer # Assuming it's in the same directory

def main():
    """
    Main function to run the Instagram browser automation.
    """
    parser = argparse.ArgumentParser(description="Automate browser interactions using Gemini.")
    parser.add_argument("--start_url", type=str, required=True, help="Initial URL to navigate to.")
    parser.add_argument("--user_goal", type=str, required=True, help="Textual description of the user's overall goal.")
    parser.add_argument("--max_steps", type=int, default=10, help="Maximum number of interaction steps.")
    # Default is True (headless). If --no-headless is present, store_false makes it False.
    parser.add_argument("--headless_browser", action='store_true', default=True, help="Run browser in headless mode. (default: True)")
    parser.add_argument("--no-headless", dest='headless_browser', action='store_false', help="Run browser in non-headless (visible) mode.")
    parser.add_argument("--step_delay", type=int, default=3, help="Seconds to wait before taking screenshot and asking Gemini (allows page to settle).")

    args = parser.parse_args()

    print("--- Starting Browser Automation ---")
    print(f"Start URL: {args.start_url}")
    print(f"User Goal: {args.user_goal}")
    print(f"Max Steps: {args.max_steps}")
    print(f"Headless Browser: {args.headless_browser}")
    print(f"Step Delay: {args.step_delay}s")
    print("------------------------------------")

    try:
        analyzer = GeminiAnalyzer() # API key is checked in its constructor
        print("GeminiAnalyzer initialized successfully.")
    except ValueError as e:
        print(f"Error initializing GeminiAnalyzer: {e}")
        print("Please ensure the GEMINI_API_KEY environment variable is set.")
        return
    except Exception as e: # Catch any other unexpected errors during analyzer init
        print(f"An unexpected error occurred during GeminiAnalyzer initialization: {e}")
        return

    # The BrowserController is used as a context manager
    try:
        with BrowserController(headless=args.headless_browser) as bc:
            print(f"BrowserController initialized (Headless: {args.headless_browser}).")
            
            print(f"Navigating to start URL: {args.start_url}...")
            bc.navigate(args.start_url) # navigate already has try-except
            if bc.page is None or bc.page.is_closed(): # Check if navigation actually failed to create/set a page
                print(f"Failed to navigate to {args.start_url}. The page is not available. Exiting.")
                return
            if "Error navigating to" in bc.page.content(): # A bit simplistic, but checks for common error messages
                 print(f"Navigation to {args.start_url} might have failed (error in page content). Exiting.")
                 return
            print("Navigation successful.")

            for i in range(args.max_steps):
                print(f"\n--- Step {i + 1} of {args.max_steps} ---")
                
                print(f"Waiting {args.step_delay}s for page to settle...")
                time.sleep(args.step_delay)

                print("Taking screenshot...")
                screenshot_bytes = bc.take_screenshot()

                if screenshot_bytes is None:
                    print("Error: Failed to take screenshot. Skipping this step.")
                    # Decide whether to continue or break. For now, let's continue.
                    if i == args.max_steps - 1: # If it's the last step and screenshot failed
                        print("Screenshot failed on the last step.")
                    continue 
                print("Screenshot taken successfully.")

                prompt_template = f"""
My overall goal is: '{args.user_goal}'.
I am currently on step {i+1} of {args.max_steps}.
This is the current page (see image).
What is the single next browser action I should take to move towards my goal?
Provide the action in one of the following formats ONLY:
- CLICK: role="<role>", name="<accessible_name>"
- CLICK: text="<text_on_element>"
- CLICK: text="<text_on_element>", exact=True
- TYPE: text="<text_to_type>" INTO: label="<label_of_input>"
- TYPE: text="<text_to_type>" INTO: placeholder="<placeholder_of_input>"
- SCROLL: direction="<down|up|top|bottom>"
- SCROLL: direction="<down|up>", pixels=<pixels_to_scroll>

If the goal seems to be achieved based on the current page, or if you are stuck or unsure how to proceed, respond with exactly 'DONE'.
If an input field needs text but you don't know what text, ask for it by responding 'NEED_INPUT: <description of what input is needed>'.
Only choose from the actions listed above. Do not provide explanations unless it is 'DONE' or 'NEED_INPUT'.
Be very specific with selectors. For example, for CLICK text, ensure the text is unique enough or use exact=True.
For TYPE, ensure the label or placeholder is correct.
For CLICK role, provide a specific and unique accessible name.
"""
                print("Asking Gemini for the next action...")
                gemini_response = analyzer.analyze_image_with_retries(
                    prompt=prompt_template, 
                    image_bytes=screenshot_bytes
                )

                if not gemini_response: # Covers None or empty string
                    print("Error: Did not receive a response from Gemini. Skipping this step.")
                    if i == args.max_steps - 1:
                        print("Gemini response failed on the last step.")
                    continue
                
                print(f"Gemini suggests: {gemini_response}")

                response_upper = gemini_response.strip().upper()

                if response_upper == "DONE":
                    print("Gemini indicated task completion.")
                    break 
                
                if response_upper.startswith("NEED_INPUT:"):
                    needed_input_description = gemini_response[len("NEED_INPUT:"):].strip()
                    print(f"Gemini needs input: {needed_input_description}")
                    # For this iteration, as specified, we just print and break.
                    # In a future version, we would prompt user and re-ask Gemini.
                    print("Halting due to 'NEED_INPUT'. Further interaction for this is not yet implemented.")
                    break

                action_taken_successfully = bc.execute_action_from_gemini(gemini_response)

                if action_taken_successfully:
                    print(f"Successfully executed: {gemini_response}")
                else:
                    print(f"Failed to execute: {gemini_response}. Continuing to next step if any.")
                    # Consider if we want to break or continue. For now, continue.
                    if i == args.max_steps - 1:
                         print("Failed to execute action on the last step.")
                
                print(f"--- End of Step {i + 1} ---")

            print("\n--- Automation Loop Finished ---")
            if i == args.max_steps -1 and response_upper != "DONE":
                 print("Reached maximum steps.")
            elif response_upper != "DONE":
                print("Loop finished for other reasons (e.g. NEED_INPUT, error).")

    except Exception as e:
        print(f"An unexpected error occurred during the main workflow: {e}")
    finally:
        print("--- Browser Automation Ended ---")


if __name__ == "__main__":
    main()
