import unittest
import os
import time # For patching sleep
from unittest.mock import patch, MagicMock, PropertyMock, call

# Adjust the path to import GeminiAnalyzer from the src directory
# This assumes tests are run from the root of the project (e.g., 'python -m unittest discover')
# or that PYTHONPATH includes the project root.
try:
    from instagram_browser_automation.src.gemini_analyzer import GeminiAnalyzer
except ImportError:
    # Fallback for cases where the above doesn't work directly (e.g. specific IDE setups)
    import sys
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) # instagram_browser_automation/
    src_path = os.path.join(project_root, 'src')
    if src_path not in sys.path:
         sys.path.insert(0, src_path)
    if project_root not in sys.path: # If 'instagram_browser_automation.src' is used for import
        sys.path.insert(0, os.path.dirname(project_root)) # Add parent of 'instagram_browser_automation'
    from instagram_browser_automation.src.gemini_analyzer import GeminiAnalyzer


# Mock the google.generativeai module at the top level of where it's imported by the module under test
# The patch should target where 'genai' is LOOKED UP, which is in the module being tested.
@patch('instagram_browser_automation.src.gemini_analyzer.genai', autospec=True)
class TestGeminiAnalyzer(unittest.TestCase):

    def setUp(self):
        # This method is called before each test.
        # mock_genai_module is passed by the class-level patch.
        # We can reset specific mocks if needed, but often the test isolation
        # provided by running each test method with fresh mocks is sufficient.
        pass

    # --- Initialization Tests ---
    def test_initialization_with_api_key_arg(self, mock_genai_module):
        """Test initialization with API key provided as an argument."""
        analyzer = GeminiAnalyzer(api_key="test_key_arg")
        mock_genai_module.configure.assert_called_once_with(api_key="test_key_arg")
        mock_genai_module.GenerativeModel.assert_called_once_with('gemini-pro-vision')
        self.assertIsNotNone(analyzer.model, "Model should be initialized.")

    @patch('instagram_browser_automation.src.gemini_analyzer.os.getenv')
    def test_initialization_with_env_var(self, mock_getenv, mock_genai_module):
        """Test initialization with API key from environment variable."""
        mock_getenv.return_value = "test_key_env"
        analyzer = GeminiAnalyzer()
        mock_getenv.assert_called_once_with("GEMINI_API_KEY")
        mock_genai_module.configure.assert_called_once_with(api_key="test_key_env")
        mock_genai_module.GenerativeModel.assert_called_once_with('gemini-pro-vision')
        self.assertIsNotNone(analyzer.model, "Model should be initialized.")

    @patch('instagram_browser_automation.src.gemini_analyzer.os.getenv')
    def test_initialization_no_api_key_raises_valueerror(self, mock_getenv, mock_genai_module):
        """Test initialization raises ValueError if no API key is found."""
        mock_getenv.return_value = None
        with self.assertRaises(ValueError) as context:
            GeminiAnalyzer()
        self.assertTrue("GEMINI_API_KEY must be provided" in str(context.exception))
        mock_genai_module.configure.assert_not_called()
        mock_genai_module.GenerativeModel.assert_not_called()

    # --- analyze_image Tests ---
    def test_analyze_image_success(self, mock_genai_module):
        """Test successful image analysis."""
        # The class-level patch already provides mock_genai_module.
        # mock_genai_module.GenerativeModel.return_value is the mock model instance.
        mock_model_instance = mock_genai_module.GenerativeModel.return_value
        
        mock_response = MagicMock()
        mock_response.text = "Expected analysis"
        
        # Mocking prompt_feedback and its block_reason property
        # Using type() with PropertyMock for attributes that are properties
        mock_prompt_feedback = MagicMock()
        type(mock_prompt_feedback).block_reason = PropertyMock(return_value=None)
        mock_response.prompt_feedback = mock_prompt_feedback
        
        # Mocking candidates
        # The actual structure of candidates might be more complex if your code delves into it.
        # For now, assume it's a list and the presence of text is the main check.
        mock_candidate = MagicMock() 
        # If your code was checking candidate.content.parts for text, you'd mock that too:
        # mock_part = MagicMock()
        # mock_part.text = "Expected analysis"
        # type(mock_candidate.content).parts = PropertyMock(return_value=[mock_part])
        type(mock_response).candidates = PropertyMock(return_value=[mock_candidate]) 

        mock_model_instance.generate_content.return_value = mock_response

        analyzer = GeminiAnalyzer(api_key="fake_key") # Initialize
        result = analyzer.analyze_image("test prompt", b"image_bytes")

        self.assertEqual(result, "Expected analysis")
        expected_image_part = {"mime_type": "image/png", "data": b"image_bytes"}
        # The content passed to generate_content should be a list
        mock_model_instance.generate_content.assert_called_once_with(["test prompt", expected_image_part])

    def test_analyze_image_success_via_parts_if_text_is_none(self, mock_genai_module):
        """Test analysis success when response.text is None but parts contain text."""
        mock_model_instance = mock_genai_module.GenerativeModel.return_value
        
        mock_response = MagicMock()
        mock_response.text = None # Simulate response.text being None
        
        mock_prompt_feedback = MagicMock()
        type(mock_prompt_feedback).block_reason = PropertyMock(return_value=None)
        mock_response.prompt_feedback = mock_prompt_feedback
        
        mock_candidate = MagicMock()
        mock_part1 = MagicMock()
        mock_part1.text = "Part 1 text. "
        mock_part2 = MagicMock()
        mock_part2.text = "Part 2 text."
        
        # Mock the content and parts structure
        mock_content = MagicMock()
        type(mock_content).parts = PropertyMock(return_value=[mock_part1, mock_part2])
        type(mock_candidate).content = PropertyMock(return_value=mock_content)
        type(mock_response).candidates = PropertyMock(return_value=[mock_candidate])

        mock_model_instance.generate_content.return_value = mock_response

        analyzer = GeminiAnalyzer(api_key="fake_key")
        result = analyzer.analyze_image("test prompt", b"image_bytes")

        self.assertEqual(result, "Part 1 text. Part 2 text.")

    def test_analyze_image_api_error(self, mock_genai_module):
        """Test handling of API error during image analysis."""
        mock_model_instance = mock_genai_module.GenerativeModel.return_value
        mock_model_instance.generate_content.side_effect = Exception("API Error")

        analyzer = GeminiAnalyzer(api_key="fake_key")
        result = analyzer.analyze_image("test prompt", b"image_bytes")

        self.assertIsNone(result, "Result should be None on API error.")
        mock_model_instance.generate_content.assert_called_once()

    def test_analyze_image_blocked_prompt(self, mock_genai_module):
        """Test handling of a prompt blocked for safety reasons."""
        mock_model_instance = mock_genai_module.GenerativeModel.return_value
        
        mock_response = MagicMock()
        mock_prompt_feedback = MagicMock()
        type(mock_prompt_feedback).block_reason = PropertyMock(return_value="SAFETY")
        mock_response.prompt_feedback = mock_prompt_feedback
        type(mock_response).text = PropertyMock(return_value=None) # Or some default text, if block_reason is primary
        type(mock_response).candidates = PropertyMock(return_value=[]) # Often empty if blocked

        mock_model_instance.generate_content.return_value = mock_response

        analyzer = GeminiAnalyzer(api_key="fake_key")
        result = analyzer.analyze_image("test prompt", b"image_bytes")

        self.assertIsNone(result, "Result should be None if prompt is blocked.")
        mock_model_instance.generate_content.assert_called_once()

    def test_analyze_image_no_text_or_candidates(self, mock_genai_module):
        """Test handling when response has no text and no candidates."""
        mock_model_instance = mock_genai_module.GenerativeModel.return_value
        
        mock_response = MagicMock()
        mock_response.text = None
        mock_prompt_feedback = MagicMock()
        type(mock_prompt_feedback).block_reason = PropertyMock(return_value=None)
        mock_response.prompt_feedback = mock_prompt_feedback
        type(mock_response).candidates = PropertyMock(return_value=[]) # No candidates

        mock_model_instance.generate_content.return_value = mock_response

        analyzer = GeminiAnalyzer(api_key="fake_key")
        result = analyzer.analyze_image("test prompt", b"image_bytes")

        self.assertIsNone(result, "Result should be None if no text and no candidates.")

    def test_analyze_image_no_text_in_candidates_parts(self, mock_genai_module):
        """Test handling when response has no text and candidates' parts also have no text."""
        mock_model_instance = mock_genai_module.GenerativeModel.return_value
        
        mock_response = MagicMock()
        mock_response.text = None
        mock_prompt_feedback = MagicMock()
        type(mock_prompt_feedback).block_reason = PropertyMock(return_value=None)
        mock_response.prompt_feedback = mock_prompt_feedback
        
        mock_candidate = MagicMock()
        mock_content = MagicMock()
        mock_part = MagicMock()
        # Simulate part.text not existing or being None
        # One way is to make 'text' a PropertyMock that raises AttributeError
        type(mock_part).text = PropertyMock(side_effect=AttributeError("no text here")) 
        type(mock_content).parts = PropertyMock(return_value=[mock_part])
        type(mock_candidate).content = PropertyMock(return_value=mock_content)
        type(mock_response).candidates = PropertyMock(return_value=[mock_candidate])

        mock_model_instance.generate_content.return_value = mock_response

        analyzer = GeminiAnalyzer(api_key="fake_key")
        result = analyzer.analyze_image("test prompt", b"image_bytes")
        self.assertIsNone(result, "Result should be None if no text available in parts.")

    # --- analyze_image_with_retries Tests ---
    @patch('instagram_browser_automation.src.gemini_analyzer.time.sleep', autospec=True)
    def test_analyze_image_with_retries_success_on_first_try(self, mock_sleep, mock_genai_module):
        """Test retry logic succeeds on the first attempt."""
        mock_model_instance = mock_genai_module.GenerativeModel.return_value
        
        mock_response = MagicMock()
        mock_response.text = "Success!"
        mock_prompt_feedback = MagicMock()
        type(mock_prompt_feedback).block_reason = PropertyMock(return_value=None)
        mock_response.prompt_feedback = mock_prompt_feedback
        type(mock_response).candidates = PropertyMock(return_value=[MagicMock()])

        mock_model_instance.generate_content.return_value = mock_response

        analyzer = GeminiAnalyzer(api_key="fake_key")
        result = analyzer.analyze_image_with_retries("prompt", b"img", retries=3, delay_seconds=1)

        self.assertEqual(result, "Success!")
        mock_model_instance.generate_content.assert_called_once()
        mock_sleep.assert_not_called()

    @patch('instagram_browser_automation.src.gemini_analyzer.time.sleep', autospec=True)
    def test_analyze_image_with_retries_success_after_failures(self, mock_sleep, mock_genai_module):
        """Test retry logic succeeds after a few failed attempts."""
        mock_model_instance = mock_genai_module.GenerativeModel.return_value
        
        mock_success_response = MagicMock()
        mock_success_response.text = "Finally succeeded"
        mock_prompt_feedback = MagicMock()
        type(mock_prompt_feedback).block_reason = PropertyMock(return_value=None)
        mock_success_response.prompt_feedback = mock_prompt_feedback
        type(mock_success_response).candidates = PropertyMock(return_value=[MagicMock()])

        mock_model_instance.generate_content.side_effect = [
            Exception("Fail1"), 
            Exception("Fail2"), 
            mock_success_response
        ]

        analyzer = GeminiAnalyzer(api_key="fake_key")
        result = analyzer.analyze_image_with_retries("prompt", b"img", retries=3, delay_seconds=1)

        self.assertEqual(result, "Finally succeeded")
        self.assertEqual(mock_model_instance.generate_content.call_count, 3)
        mock_sleep.assert_has_calls([call(1), call(1)], any_order=False)
        self.assertEqual(mock_sleep.call_count, 2)

    @patch('instagram_browser_automation.src.gemini_analyzer.time.sleep', autospec=True)
    def test_analyze_image_with_retries_all_failures(self, mock_sleep, mock_genai_module):
        """Test retry logic when all attempts fail."""
        mock_model_instance = mock_genai_module.GenerativeModel.return_value
        mock_model_instance.generate_content.side_effect = Exception("Persistent API Error")

        analyzer = GeminiAnalyzer(api_key="fake_key")
        result = analyzer.analyze_image_with_retries("prompt", b"img", retries=3, delay_seconds=1)

        self.assertIsNone(result)
        self.assertEqual(mock_model_instance.generate_content.call_count, 3)
        mock_sleep.assert_has_calls([call(1), call(1)], any_order=False)
        self.assertEqual(mock_sleep.call_count, 2)

if __name__ == '__main__':
    # This allows running the tests directly from this file using `python path/to/test_gemini_analyzer.py`
    # However, it's generally better to run tests using the unittest discovery mechanism
    # from the project root: `python -m unittest discover tests` or `python -m unittest tests.test_gemini_analyzer`
    # The `argv` and `exit` parameters are adjusted for typical script execution.
    unittest.main()
