# This file will contain the logic for interacting with the Gemini API.
# It will take image data from the browser controller and send it to Gemini for analysis.

import google.generativeai as genai
import os
from PIL import Image # For image loading in example
import io # For converting PIL Image to bytes in example
import time
from typing import Optional, Dict, Any, List # Added Dict, Any, List for type hinting

# Import for potential API errors, though specific error types might vary
# For now, using a general Exception for Google API errors.
# from google.api_core import exceptions as google_exceptions

class GeminiAnalyzer:
    """
    Interacts with the Google Gemini API to analyze images.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initializes the GeminiAnalyzer.

        Args:
            api_key: The Gemini API key. If None, it's read from the
                     GEMINI_API_KEY environment variable.
        Raises:
            ValueError: If the API key is not provided and not found in environment variables.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY must be provided or set as an environment variable.")

        genai.configure(api_key=self.api_key)
        # Using 'gemini-pro-vision' as specified, ensure this model is available.
        # For future compatibility, one might check for the latest stable vision model.
        self.model = genai.GenerativeModel('gemini-pro-vision')

    def analyze_image(self, prompt: str, image_bytes: bytes) -> Optional[str]:
        """
        Analyzes an image using the Gemini API with a given prompt.

        Args:
            prompt: The text prompt to guide the image analysis.
            image_bytes: The image data in bytes.

        Returns:
            The analysis text from Gemini if successful, None otherwise.
        """
        image_part: Dict[str, Any] = {
            "mime_type": "image/png",  # Assuming PNG, adjust if other formats are common
            "data": image_bytes
        }

        # The content for gemini-pro-vision should be a list
        contents: List[Any] = [prompt, image_part]

        try:
            response = self.model.generate_content(contents)

            # Check for prompt feedback and block reasons
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                print(f"Analysis blocked due to: {response.prompt_feedback.block_reason}")
                return None

            # Ensure candidates exist and have content
            if not response.candidates:
                print("Warning: No candidates returned from Gemini.")
                return None
            
            # Accessing text directly from response as per common usage for gemini-pro-vision
            # If the structure is different (e.g. parts), this needs adjustment.
            # Based on documentation, response.text should be the primary way for simple text.
            if hasattr(response, 'text'):
                return response.text
            else:
                # Fallback if .text is not available, try to get it from parts
                # This is a common pattern for multi-part responses, but
                # gemini-pro-vision with a text prompt and one image usually yields .text
                if response.candidates[0].content and response.candidates[0].content.parts:
                    return "".join(part.text for part in response.candidates[0].content.parts if hasattr(part, 'text'))
                print("Warning: No text found in Gemini response.")
                return None

        # except google_exceptions.GoogleAPIError as e: # More specific error
        # print(f"Gemini API error: {e}")
        except Exception as e: # General fallback
            print(f"An error occurred during Gemini image analysis: {e}")
            return None

    def analyze_image_with_retries(self, prompt: str, image_bytes: bytes, retries: int = 3, delay_seconds: int = 5) -> Optional[str]:
        """
        Calls analyze_image with retries upon failure.

        Args:
            prompt: The text prompt.
            image_bytes: The image data in bytes.
            retries: Number of times to retry.
            delay_seconds: Delay between retries in seconds.

        Returns:
            The analysis text if successful, None otherwise.
        """
        for attempt in range(retries):
            print(f"Attempt {attempt + 1} of {retries} to analyze image...")
            result = self.analyze_image(prompt, image_bytes)
            if result:
                return result
            if attempt < retries - 1: # Don't sleep after the last attempt
                print(f"Analysis failed. Retrying in {delay_seconds} seconds...")
                time.sleep(delay_seconds)
            else:
                print("All retries failed.")
        return None

if __name__ == '__main__':
    print("Gemini Analyzer Example Usage")
    print("-----------------------------")
    print("NOTE: This example requires the GEMINI_API_KEY environment variable to be set.")
    print("It also attempts to load 'playwright_home.png' from the parent directory (../playwright_home.png).")
    print("Ensure this image exists or modify the path.\n")

    # Attempt to instantiate the analyzer
    analyzer: Optional[GeminiAnalyzer] = None
    try:
        analyzer = GeminiAnalyzer()
        print("GeminiAnalyzer initialized successfully.")
    except ValueError as e:
        print(f"Error initializing GeminiAnalyzer: {e}")
        print("Please set the GEMINI_API_KEY environment variable.")
    except Exception as e: # Catch other potential init errors (e.g., genai configuration)
        print(f"An unexpected error occurred during GeminiAnalyzer initialization: {e}")

    if analyzer:
        # Try to load an image (e.g., the one saved by browser_controller.py)
        # The script is in src/, so playwright_home.png would be in the root if saved there.
        # Adjust path if script is run from a different location or image is elsewhere.
        image_path = "../playwright_home.png" # Assuming src/gemini_analyzer.py
        
        image_bytes: Optional[bytes] = None
        try:
            # Ensure Pillow is used to open, then convert to bytes
            # This is for the example; in practice, image_bytes come from screenshot
            with Image.open(image_path) as img:
                # Convert to PNG bytes
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG')
                image_bytes = img_byte_arr.getvalue()
            print(f"Successfully loaded image from: {image_path}")
        except FileNotFoundError:
            print(f"Error: Image file not found at '{image_path}'.")
            print("Please ensure 'playwright_home.png' exists in the project root directory,")
            print("or run the browser_controller.py example first to create it.")
            print("Alternatively, replace 'image_path' with a path to any PNG image.")
        except Exception as e:
            print(f"Error loading image: {e}")

        if image_bytes:
            prompt_text = "Describe this webpage. What is its main purpose?"
            print(f"\nAnalyzing image with prompt: '{prompt_text}'")
            
            analysis_result = analyzer.analyze_image_with_retries(
                prompt=prompt_text,
                image_bytes=image_bytes
            )

            if analysis_result:
                print("\n--- Analysis Result ---")
                print(analysis_result)
                print("-----------------------")
            else:
                print("\nImage analysis failed after retries.")
        else:
            print("\nSkipping image analysis as image could not be loaded.")

    print("\nExample usage finished.")
