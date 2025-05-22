# This file will contain the browser automation logic.
# It will use Playwright to interact with the Instagram website.
# Functions will include logging in, navigating to profiles, and extracting data.

import re
import time # For example usage
from typing import Dict, Any, Pattern, Optional # Added Optional for type hints
from playwright.sync_api import sync_playwright, Playwright, Browser, Page
# Attempt to import TimeoutError specifically, otherwise use generic Exception
try:
    from playwright._impl._api_types import TimeoutError as PlaywrightTimeoutError
except ImportError:
    PlaywrightTimeoutError = Exception # Fallback to generic Exception


class BrowserController:
    """
    Manages browser interactions using Playwright.
    Provides methods for navigation, taking screenshots, and getting page content.
    """

    def __init__(self, headless: bool = True):
        """
        Initializes the BrowserController.

        Args:
            headless: If True, runs the browser in headless mode. Defaults to True.
        """
        self.playwright: Optional[Playwright] = sync_playwright().start()
        self.browser: Browser = self.playwright.chromium.launch(headless=headless)
        self.page: Optional[Page] = None

    def navigate(self, url: str):
        """
        Navigates to the specified URL.

        Args:
            url: The URL to navigate to.
        """
        try:
            if self.page is None or self.page.is_closed():
                if self.browser: # Ensure browser is available
                    self.page = self.browser.new_page()
                else:
                    print("Error: Browser is not initialized.")
                    return
            if self.page: # Ensure page is available
                self.page.goto(url)
            else:
                print("Error: Page could not be created.")
        except Exception as e:
            print(f"Error navigating to {url}: {e}")

    def take_screenshot(self) -> Optional[bytes]:
        """
        Takes a full-page screenshot of the current page.

        Returns:
            Screenshot bytes if successful, None otherwise.
        """
        if self.page is not None and not self.page.is_closed():
            try:
                screenshot_bytes = self.page.screenshot(full_page=True)
                return screenshot_bytes
            except Exception as e:
                print(f"Error taking screenshot: {e}")
                return None
        else:
            print("Warning: Page is not available to take a screenshot.")
            return None

    def get_current_page_content(self) -> Optional[str]:
        """
        Gets the HTML content of the current page.

        Returns:
            Page content as a string if successful, None otherwise.
        """
        if self.page is not None and not self.page.is_closed():
            try:
                return self.page.content()
            except Exception as e:
                print(f"Error getting page content: {e}")
                return None
        else:
            print("Warning: Page is not available to get content.")
            return None

    def click_element_by_text(self, text_to_find: str, use_exact: bool = False, timeout: int = 5000) -> bool:
        """
        Clicks an element identified by its text content.

        Args:
            text_to_find: The text to search for within an element.
            use_exact: Whether to match the text exactly or allow partial matches.
            timeout: Maximum time in milliseconds to wait for the element.

        Returns:
            True if click was successful, False otherwise.
        """
        if not self.page or self.page.is_closed():
            print("Error: Page is not available.")
            return False
        try:
            locator = self.page.get_by_text(text_to_find, exact=use_exact).first
            locator.click(timeout=timeout)
            print(f"Clicked element with text: '{text_to_find}' (exact: {use_exact})")
            return True
        except PlaywrightTimeoutError:
            print(f"TimeoutError: Element with text '{text_to_find}' not found or not clickable within {timeout}ms.")
            return False
        except Exception as e:
            print(f"Error clicking element with text '{text_to_find}': {e}")
            return False

    def click_element_by_role(self, role: str, name: str, timeout: int = 5000) -> bool:
        """
        Clicks an element identified by its ARIA role and accessible name.

        Args:
            role: The ARIA role of the element (e.g., 'button', 'link').
            name: The accessible name of the element (case-insensitive regex).
            timeout: Maximum time in milliseconds to wait for the element.

        Returns:
            True if click was successful, False otherwise.
        """
        if not self.page or self.page.is_closed():
            print("Error: Page is not available.")
            return False
        try:
            # Using re.compile for case-insensitive and flexible matching
            locator = self.page.get_by_role(role, name=re.compile(name, re.IGNORECASE)).first
            locator.click(timeout=timeout)
            print(f"Clicked element with role '{role}' and name matching regex '{name}'")
            return True
        except PlaywrightTimeoutError:
            print(f"TimeoutError: Element with role '{role}' and name regex '{name}' not found or not clickable within {timeout}ms.")
            return False
        except Exception as e:
            print(f"Error clicking element with role '{role}' and name regex '{name}': {e}")
            return False

    def type_into_element_by_label(self, label_text: str, text_to_type: str, timeout: int = 5000) -> bool:
        """
        Types text into an input element identified by its label.

        Args:
            label_text: The text of the label associated with the input element.
            text_to_type: The text to type into the input element.
            timeout: Maximum time in milliseconds to wait for the element.

        Returns:
            True if typing was successful, False otherwise.
        """
        if not self.page or self.page.is_closed():
            print("Error: Page is not available.")
            return False
        try:
            locator = self.page.get_by_label(label_text)
            locator.fill(text_to_type, timeout=timeout)
            print(f"Typed '{text_to_type}' into element with label '{label_text}'")
            return True
        except PlaywrightTimeoutError:
            print(f"TimeoutError: Element with label '{label_text}' not found or not editable within {timeout}ms.")
            return False
        except Exception as e:
            print(f"Error typing into element with label '{label_text}': {e}")
            return False

    def type_into_element_by_placeholder(self, placeholder_text: str, text_to_type: str, timeout: int = 5000) -> bool:
        """
        Types text into an input element identified by its placeholder text.

        Args:
            placeholder_text: The placeholder text of the input element.
            text_to_type: The text to type into the input element.
            timeout: Maximum time in milliseconds to wait for the element.

        Returns:
            True if typing was successful, False otherwise.
        """
        if not self.page or self.page.is_closed():
            print("Error: Page is not available.")
            return False
        try:
            locator = self.page.get_by_placeholder(placeholder_text)
            locator.fill(text_to_type, timeout=timeout)
            print(f"Typed '{text_to_type}' into element with placeholder '{placeholder_text}'")
            return True
        except PlaywrightTimeoutError:
            print(f"TimeoutError: Element with placeholder '{placeholder_text}' not found or not editable within {timeout}ms.")
            return False
        except Exception as e:
            print(f"Error typing into element with placeholder '{placeholder_text}': {e}")
            return False

    def scroll_page(self, direction: str, pixels: int = 0) -> bool:
        """
        Scrolls the page in a given direction.

        Args:
            direction: "up", "down", "top", or "bottom".
            pixels: Number of pixels to scroll for "up" or "down".
                    Defaults to window.innerHeight if 0.

        Returns:
            True if scrolling was successful, False otherwise.
        """
        if not self.page or self.page.is_closed():
            print("Error: Page is not available.")
            return False
        try:
            js_command = ""
            if direction == "down":
                js_command = f"window.scrollBy(0, {pixels if pixels else 'window.innerHeight'});"
            elif direction == "up":
                js_command = f"window.scrollBy(0, -{pixels if pixels else 'window.innerHeight'});"
            elif direction == "top":
                js_command = "window.scrollTo(0, 0);"
            elif direction == "bottom":
                js_command = "window.scrollTo(0, document.body.scrollHeight);"
            else:
                print(f"Error: Invalid scroll direction '{direction}'. Must be 'up', 'down', 'top', or 'bottom'.")
                return False
            
            self.page.evaluate(js_command)
            print(f"Scrolled page {direction}" + (f" by {pixels} pixels" if pixels and direction in ["up", "down"] else ""))
            return True
        except Exception as e:
            print(f"Error scrolling page {direction}: {e}")
            return False

    def execute_action_from_gemini(self, gemini_instruction: str) -> bool:
        """
        Parses a Gemini instruction string and executes the corresponding browser action.

        Args:
            gemini_instruction: A string command from Gemini. Examples:
                - "CLICK: text='Get started'"
                - "CLICK: text='Documentation', exact=True"
                - "CLICK: role=button, name='Submit Form'"
                - "TYPE: text='hello world' INTO: label='Username'"
                - "TYPE: text='search query' INTO: placeholder='Search'"
                - "SCROLL: direction=down"
                - "SCROLL: direction=up, pixels=300"
                - "SCROLL: direction=top"
                - "SCROLL: direction=bottom"

        Returns:
            True if an action was successfully parsed and executed, False otherwise.
        """
        print(f"\nExecuting Gemini instruction: '{gemini_instruction}'")

        # CLICK by text
        click_text_match = re.match(r"CLICK: text='(?P<text>[^']+)'(?:, exact=(?P<exact>True|False))?", gemini_instruction, re.IGNORECASE)
        if click_text_match:
            params = click_text_match.groupdict()
            text_to_find = params['text']
            use_exact = params['exact'] == 'True' if params['exact'] else False
            success = self.click_element_by_text(text_to_find, use_exact=use_exact)
            print(f"Action 'CLICK by text: {text_to_find}' {'succeeded' if success else 'failed'}")
            return success

        # CLICK by role
        click_role_match = re.match(r"CLICK: role=(?P<role>[^,]+), name='(?P<name>[^']+)'", gemini_instruction, re.IGNORECASE)
        if click_role_match:
            params = click_role_match.groupdict()
            role = params['role'].strip()
            name = params['name']
            success = self.click_element_by_role(role, name)
            print(f"Action 'CLICK by role: {role}, name: {name}' {'succeeded' if success else 'failed'}")
            return success

        # TYPE into label
        type_label_match = re.match(r"TYPE: text='(?P<text_to_type>[^']+)' INTO: label='(?P<label>[^']+)'", gemini_instruction, re.IGNORECASE)
        if type_label_match:
            params = type_label_match.groupdict()
            text_to_type = params['text_to_type']
            label_text = params['label']
            success = self.type_into_element_by_label(label_text, text_to_type)
            print(f"Action 'TYPE into label: {label_text}' {'succeeded' if success else 'failed'}")
            return success

        # TYPE into placeholder
        type_placeholder_match = re.match(r"TYPE: text='(?P<text_to_type>[^']+)' INTO: placeholder='(?P<placeholder>[^']+)'", gemini_instruction, re.IGNORECASE)
        if type_placeholder_match:
            params = type_placeholder_match.groupdict()
            text_to_type = params['text_to_type']
            placeholder_text = params['placeholder']
            success = self.type_into_element_by_placeholder(placeholder_text, text_to_type)
            print(f"Action 'TYPE into placeholder: {placeholder_text}' {'succeeded' if success else 'failed'}")
            return success

        # SCROLL
        scroll_match = re.match(r"SCROLL: direction=(?P<direction>down|up|top|bottom)(?:, pixels=(?P<pixels>\d+))?", gemini_instruction, re.IGNORECASE)
        if scroll_match:
            params = scroll_match.groupdict()
            direction = params['direction']
            pixels = int(params['pixels']) if params['pixels'] else 0
            success = self.scroll_page(direction, pixels)
            print(f"Action 'SCROLL: {direction}, pixels: {pixels}' {'succeeded' if success else 'failed'}")
            return success
        
        print(f"Error: Could not parse Gemini instruction: '{gemini_instruction}'")
        return False

    def close(self):
        """
        Closes the browser and stops Playwright.
        """
        if self.browser is not None and self.browser.is_connected():
            self.browser.close()
        if self.playwright is not None:
            self.playwright.stop()
            self.playwright = None  # Prevent trying to stop it multiple times

    def __enter__(self):
        """
        Allows the class to be used as a context manager.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Ensures resources are cleaned up when exiting the context.
        """
        self.close()

if __name__ == '__main__':
    # Example Usage
    # Note: This requires Playwright browsers to be installed.
    # Run `playwright install` in your terminal if you haven't already.
    # Use headless=False to see the browser interactions.
    with BrowserController(headless=True) as bc: 
        print("Navigating to Playwright homepage...")
        bc.navigate("https://playwright.dev/python")
        
        print("\nTaking initial screenshot...")
        screenshot = bc.take_screenshot()
        if bc.page: # Ensure page is available before operations
            if screenshot:
                with open("playwright_home_initial.png", "wb") as f:
                    f.write(screenshot)
                print("Initial screenshot saved to playwright_home_initial.png")
            else:
                print("Failed to take initial screenshot.")
            
            page_content = bc.get_current_page_content()
            if page_content:
                print(f"Initial page title: {bc.page.title()}")
            else:
                print("Failed to get initial page content.")

            # Demonstrate execute_action_from_gemini
            print("\n--- Testing execute_action_from_gemini ---")

            action1_success = bc.execute_action_from_gemini("CLICK: text='Get started'")
            print(f"Result of 'CLICK: text='Get started'': {action1_success}")
            if action1_success and bc.page: # Check page again as it might have navigated
                print(f"Page title after 'Get started' click: {bc.page.title()}")
                time.sleep(2) # Allow page to load

            action2_success = bc.execute_action_from_gemini("SCROLL: direction=down, pixels=500")
            print(f"Result of 'SCROLL: direction=down, pixels=500': {action2_success}")
            time.sleep(1)

            action3_success = bc.execute_action_from_gemini("SCROLL: direction=top")
            print(f"Result of 'SCROLL: direction=top': {action3_success}")
            time.sleep(1)

            # Example of typing into the search bar on Playwright's site
            # The placeholder for the search bar (as of late 2023/early 2024) is "Search"
            # This might change, adjust if needed.
            type_action_text = "python"
            type_action_placeholder = "Search" # Placeholder for search on Playwright docs
            
            # Check if the search bar is present before attempting to type
            # This is a simplified check; a real scenario might need more robust element presence check
            if bc.page.query_selector(f"input[placeholder='{type_action_placeholder}']"):
                print(f"\nAttempting to type '{type_action_text}' into placeholder '{type_action_placeholder}'...")
                action4_success = bc.execute_action_from_gemini(f"TYPE: text='{type_action_text}' INTO: placeholder='{type_action_placeholder}'")
                print(f"Result of TYPE action: {action4_success}")
                if action4_success:
                    # Take a screenshot to see the typed text
                    screenshot_after_type = bc.take_screenshot()
                    if screenshot_after_type:
                        with open("playwright_after_type.png", "wb") as f:
                            f.write(screenshot_after_type)
                        print("Screenshot after typing saved to playwright_after_type.png")
                time.sleep(1)
            else:
                print(f"\nSearch bar with placeholder '{type_action_placeholder}' not found. Skipping TYPE action example.")

            # Example of a failing action (e.g., element not found)
            print("\nTesting a failing action (element not found)...")
            action_fail_success = bc.execute_action_from_gemini("CLICK: text='NonExistentButton123'")
            print(f"Result of 'CLICK: text='NonExistentButton123'': {action_fail_success}")

            print("\n--- End of execute_action_from_gemini tests ---")

        else:
            print("Browser page was not initialized correctly. Skipping actions.")

    # Test that playwright is stopped
    print("\nTesting Playwright cleanup...")
    try:
        # Accessing bc.playwright directly after context exit might be tricky if it's truly cleaned.
        # The goal is to ensure no operations can be performed.
        if bc.playwright is None:
             print("Playwright context manager successfully stopped (playwright attribute is None).")
        else:
            # Try a simple operation that would fail if closed
            bc.navigate("http://example.com") # This should ideally not work or error out
            print("Warning: Playwright instance might not be fully closed if navigation call above seems to work.")
    except Exception as e:
        print(f"Playwright context manager successfully stopped (error on reuse as expected): {e}")
    
    print("\nExample usage finished.")
