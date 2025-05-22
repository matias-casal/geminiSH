import unittest
import re
from unittest.mock import patch, MagicMock, call, PropertyMock

# Adjust path for importing BrowserController from src
try:
    from instagram_browser_automation.src.browser_controller import BrowserController
    # Attempt to import TimeoutError, try common locations
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    except ImportError: # Fallback for older Playwright or different structure
        from playwright._impl._api_types import TimeoutError as PlaywrightTimeoutError
except ImportError:
    import sys
    import os
    # Assuming tests/test_browser_controller.py
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) # instagram_browser_automation/
    src_path = os.path.join(project_root, 'src')
    if src_path not in sys.path:
         sys.path.insert(0, src_path)
    
    # Add parent of project_root for 'instagram_browser_automation.src...' if that's how you import
    # This covers the case where the module is imported as `from instagram_browser_automation.src...`
    # when 'instagram_browser_automation' is the top-level package recognized by Python.
    parent_of_project_root = os.path.dirname(project_root)
    if parent_of_project_root not in sys.path:
        sys.path.insert(0, parent_of_project_root)

    from instagram_browser_automation.src.browser_controller import BrowserController
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    except ImportError:
        from playwright._impl._api_types import TimeoutError as PlaywrightTimeoutError


# Patch sync_playwright at the location where it's imported in browser_controller.py
# The patch should target 'instagram_browser_automation.src.browser_controller.sync_playwright'
# because that's where BrowserController looks up 'sync_playwright'.
@patch('instagram_browser_automation.src.browser_controller.sync_playwright', autospec=True)
class TestBrowserController(unittest.TestCase):

    def setUp(self, mock_sync_playwright_constructor):
        # mock_sync_playwright_constructor is the patched 'sync_playwright' function/module.
        # .return_value is the result of calling sync_playwright(), which is the Playwright context manager.
        # .start() is called on that manager.
        self.mock_playwright_manager = mock_sync_playwright_constructor.return_value.start.return_value
        self.mock_browser = self.mock_playwright_manager.chromium.launch.return_value
        self.mock_page = self.mock_browser.new_page.return_value
        self.mock_page.is_closed.return_value = False # Default assumption for most tests

        # Instantiate controller AFTER sync_playwright is patched and mocks are set up
        self.controller = BrowserController(headless=True)
        # BrowserController's __init__ calls sync_playwright().start(), so the mocks are used.

    # --- Initialization Test ---
    def test_initialization(self, mock_sync_playwright_constructor): 
        # mock_sync_playwright_constructor is from class decorator, used by setUp
        self.mock_playwright_manager.chromium.launch.assert_called_once_with(headless=True)
        self.assertIsNone(self.controller.page, "Controller's page should be None initially.")
        # Ensure the controller's internal playwright and browser are the mocked ones
        self.assertEqual(self.controller.playwright, self.mock_playwright_manager)
        self.assertEqual(self.controller.browser, self.mock_browser)

    # --- Navigation Tests ---
    def test_navigate_new_page(self, mock_sync_playwright_constructor):
        self.assertIsNone(self.controller.page, "Page should be None before first navigation.")
        self.controller.navigate("http://example.com")
        self.mock_browser.new_page.assert_called_once()
        self.mock_page.goto.assert_called_once_with("http://example.com")
        self.assertEqual(self.controller.page, self.mock_page)

    def test_navigate_existing_page(self, mock_sync_playwright_constructor):
        self.controller.page = self.mock_page # Pre-set an existing page
        self.mock_browser.new_page.reset_mock() # Reset from initial setup if any

        self.controller.navigate("http://anotherexample.com")
        self.mock_browser.new_page.assert_not_called() # Should not create a new page
        self.mock_page.goto.assert_called_once_with("http://anotherexample.com")

    def test_navigate_page_is_closed(self, mock_sync_playwright_constructor):
        self.controller.page = self.mock_page
        self.mock_page.is_closed.return_value = True # Simulate page was closed

        self.controller.navigate("http://example.com/closed")
        self.mock_browser.new_page.assert_called_once() # Should create a new page
        # The mock_page assigned in setUp is the one new_page returns.
        self.mock_page.goto.assert_called_once_with("http://example.com/closed")

    def test_navigate_handles_exception(self, mock_sync_playwright_constructor):
        self.controller.page = self.mock_page
        self.mock_page.goto.side_effect = PlaywrightTimeoutError("Navigation failed due to timeout")
        
        with patch('builtins.print') as mock_print:
            self.controller.navigate("http://fail.com")
        
        self.mock_page.goto.assert_called_once_with("http://fail.com")
        mock_print.assert_any_call("Error navigating to http://fail.com: Navigation failed due to timeout")

    # --- Screenshot Tests ---
    def test_take_screenshot_success(self, mock_sync_playwright_constructor):
        self.controller.page = self.mock_page
        self.mock_page.screenshot.return_value = b"screenshot_data"
        
        result = self.controller.take_screenshot()
        
        self.assertEqual(result, b"screenshot_data")
        self.mock_page.screenshot.assert_called_once_with(full_page=True)

    def test_take_screenshot_no_page(self, mock_sync_playwright_constructor):
        self.controller.page = None
        with patch('builtins.print') as mock_print:
            result = self.controller.take_screenshot()
        
        self.assertIsNone(result)
        mock_print.assert_any_call("Warning: Page is not available to take a screenshot.")
        self.mock_page.screenshot.assert_not_called()

    def test_take_screenshot_failure(self, mock_sync_playwright_constructor):
        self.controller.page = self.mock_page
        self.mock_page.screenshot.side_effect = Exception("Screenshot failed")
        with patch('builtins.print') as mock_print:
            result = self.controller.take_screenshot()
        self.assertIsNone(result)
        mock_print.assert_any_call("Error taking screenshot: Screenshot failed")

    # --- Get Content Tests ---
    def test_get_current_page_content_success(self, mock_sync_playwright_constructor):
        self.controller.page = self.mock_page
        self.mock_page.content.return_value = "<html>Page Content</html>"
        
        result = self.controller.get_current_page_content()
        
        self.assertEqual(result, "<html>Page Content</html>")
        self.mock_page.content.assert_called_once()

    def test_get_current_page_content_no_page(self, mock_sync_playwright_constructor):
        self.controller.page = None
        with patch('builtins.print') as mock_print:
            result = self.controller.get_current_page_content()
        
        self.assertIsNone(result)
        mock_print.assert_any_call("Warning: Page is not available to get content.")
        self.mock_page.content.assert_not_called()

    def test_get_current_page_content_failure(self, mock_sync_playwright_constructor):
        self.controller.page = self.mock_page
        self.mock_page.content.side_effect = Exception("Content fetch failed")
        with patch('builtins.print') as mock_print:
            result = self.controller.get_current_page_content()
        self.assertIsNone(result)
        mock_print.assert_any_call("Error getting page content: Content fetch failed")

    # --- Close Test ---
    def test_close(self, mock_sync_playwright_constructor):
        type(self.mock_browser).is_connected = PropertyMock(return_value=True)
        self.controller.close()
        self.mock_browser.close.assert_called_once()
        self.mock_playwright_manager.stop.assert_called_once()
        self.assertIsNone(self.controller.playwright, "Playwright instance should be None after close.")

    # --- Context Manager Test ---
    def test_context_manager_calls_close(self, mock_sync_playwright_constructor):
        # Test with the instance from setUp
        self.controller.__exit__(None, None, None)
        # Check if the close method of the *browser* was called,
        # as self.controller.close() is the method under test.
        # If self.controller.close() is mocked, we test if it's called.
        # Here, we test the effect of __exit__ calling the real close().
        self.mock_browser.close.assert_called_once()
        self.mock_playwright_manager.stop.assert_called_once()

    # --- Action Methods Tests ---
    # --- click_element_by_text ---
    def test_click_element_by_text_success(self, mock_sync_playwright_constructor):
        self.controller.page = self.mock_page
        mock_locator = self.mock_page.get_by_text.return_value.first
        
        result = self.controller.click_element_by_text("Click Me", use_exact=False, timeout=3000)
        
        self.assertTrue(result)
        self.mock_page.get_by_text.assert_called_once_with("Click Me", exact=False)
        mock_locator.click.assert_called_once_with(timeout=3000)

    def test_click_element_by_text_failure_not_found(self, mock_sync_playwright_constructor):
        self.controller.page = self.mock_page
        mock_locator = self.mock_page.get_by_text.return_value.first
        mock_locator.click.side_effect = PlaywrightTimeoutError("Element not found")
        
        with patch('builtins.print') as mock_print:
            result = self.controller.click_element_by_text("NonExistent")
        
        self.assertFalse(result)
        mock_print.assert_any_call("TimeoutError: Element with text 'NonExistent' not found or not clickable within 5000ms.")

    # --- click_element_by_role ---
    def test_click_element_by_role_success(self, mock_sync_playwright_constructor):
        self.controller.page = self.mock_page
        mock_locator = self.mock_page.get_by_role.return_value.first
        
        result = self.controller.click_element_by_role("button", "Submit Button", timeout=4000)
        
        self.assertTrue(result)
        self.mock_page.get_by_role.assert_called_once()
        args, kwargs = self.mock_page.get_by_role.call_args
        self.assertEqual(args[0], "button")
        self.assertIsInstance(kwargs['name'], re.Pattern)
        self.assertEqual(kwargs['name'].pattern, "Submit Button")
        self.assertEqual(kwargs['name'].flags, re.IGNORECASE)
        mock_locator.click.assert_called_once_with(timeout=4000)

    # --- type_into_element_by_label ---
    def test_type_into_element_by_label_success(self, mock_sync_playwright_constructor):
        self.controller.page = self.mock_page
        mock_locator = self.mock_page.get_by_label.return_value
        
        result = self.controller.type_into_element_by_label("Username", "testuser", timeout=2500)
        
        self.assertTrue(result)
        self.mock_page.get_by_label.assert_called_once_with("Username")
        mock_locator.fill.assert_called_once_with("testuser", timeout=2500)

    # --- type_into_element_by_placeholder ---
    def test_type_into_element_by_placeholder_success(self, mock_sync_playwright_constructor):
        self.controller.page = self.mock_page
        mock_locator = self.mock_page.get_by_placeholder.return_value
        
        result = self.controller.type_into_element_by_placeholder("Search...", "query text", timeout=3500)
        
        self.assertTrue(result)
        self.mock_page.get_by_placeholder.assert_called_once_with("Search...")
        mock_locator.fill.assert_called_once_with("query text", timeout=3500)

    # --- scroll_page ---
    def test_scroll_page_success(self, mock_sync_playwright_constructor):
        self.controller.page = self.mock_page
        
        for direction in ["down", "up", "top", "bottom"]:
            self.mock_page.evaluate.reset_mock()
            pixels = 100 if direction in ["down", "up"] else 0
            result = self.controller.scroll_page(direction, pixels=pixels)
            self.assertTrue(result)
            
            expected_js = ""
            if direction == "down": expected_js = f"window.scrollBy(0, {pixels if pixels else 'window.innerHeight'});"
            elif direction == "up": expected_js = f"window.scrollBy(0, -{pixels if pixels else 'window.innerHeight'});"
            elif direction == "top": expected_js = "window.scrollTo(0, 0);"
            elif direction == "bottom": expected_js = "window.scrollTo(0, document.body.scrollHeight);"
            
            self.mock_page.evaluate.assert_called_once_with(expected_js)

    # --- execute_action_from_gemini Tests ---
    @patch.object(BrowserController, 'click_element_by_text', return_value=True, autospec=True)
    def test_execute_gemini_click_text(self, mock_click_text, mock_sync_playwright_constructor):
        self.controller.page = self.mock_page
        result = self.controller.execute_action_from_gemini("CLICK: text='Login'")
        self.assertTrue(result)
        mock_click_text.assert_called_once_with(self.controller, "Login", use_exact=False)

    @patch.object(BrowserController, 'click_element_by_role', return_value=True, autospec=True)
    def test_execute_gemini_click_role(self, mock_click_role, mock_sync_playwright_constructor):
        self.controller.page = self.mock_page
        result = self.controller.execute_action_from_gemini("CLICK: role=button, name='Sign Up'")
        self.assertTrue(result)
        mock_click_role.assert_called_once_with(self.controller, "button", "Sign Up")

    @patch.object(BrowserController, 'type_into_element_by_label', return_value=True, autospec=True)
    def test_execute_gemini_type_label(self, mock_type_label, mock_sync_playwright_constructor):
        self.controller.page = self.mock_page
        result = self.controller.execute_action_from_gemini("TYPE: text='user@example.com' INTO: label='Email Address'")
        self.assertTrue(result)
        mock_type_label.assert_called_once_with(self.controller, "Email Address", "user@example.com")

    @patch.object(BrowserController, 'type_into_element_by_placeholder', return_value=True, autospec=True)
    def test_execute_gemini_type_placeholder(self, mock_type_placeholder, mock_sync_playwright_constructor):
        self.controller.page = self.mock_page
        result = self.controller.execute_action_from_gemini("TYPE: text='My Query' INTO: placeholder='Search here...'")
        self.assertTrue(result)
        mock_type_placeholder.assert_called_once_with(self.controller, "Search here...", "My Query")

    @patch.object(BrowserController, 'scroll_page', return_value=True, autospec=True)
    def test_execute_gemini_scroll(self, mock_scroll, mock_sync_playwright_constructor):
        self.controller.page = self.mock_page
        result = self.controller.execute_action_from_gemini("SCROLL: direction=down")
        self.assertTrue(result)
        mock_scroll.assert_called_once_with(self.controller, "down", 0)

    def test_execute_gemini_invalid_command(self, mock_sync_playwright_constructor):
        self.controller.page = self.mock_page
        with patch('builtins.print') as mock_print:
            result = self.controller.execute_action_from_gemini("UNKNOWN: command='do something'")
        self.assertFalse(result)
        mock_print.assert_any_call("Error: Could not parse Gemini instruction: 'UNKNOWN: command='do something''")

    @patch.object(BrowserController, 'click_element_by_text', return_value=False, autospec=True)
    def test_execute_gemini_action_method_fails(self, mock_click_text_fails, mock_sync_playwright_constructor):
        self.controller.page = self.mock_page
        result = self.controller.execute_action_from_gemini("CLICK: text='A button that will fail'")
        self.assertFalse(result)
        mock_click_text_fails.assert_called_once_with(self.controller, "A button that will fail", use_exact=False)

if __name__ == '__main__':
    unittest.main()
