import pyautogui
import os
import uuid
import screeninfo
from output_manager import OutputManager

output_manager = OutputManager()

DEBUG = os.getenv('DEBUG')

def take_screenshot(monitor_index=None):
    """
    This function takes a screenshot of one or all monitors and saves it to the cache directory. It is used when the user refers to what is visible on the screen or asks something like "what do you see" on the computer or screen.
    
    Parameters:
    monitor_index (int, optional): The index of the monitor to capture. If not provided, captures all monitors.

    Returns:
    files: The screenshots taken.
    """
    try:
        # Detect the number of screens
        monitors = screeninfo.get_monitors()
        screenshots = []
        save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'cache')
        
        # Check if the save path exists, if not, create it
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        
        if monitor_index is not None:
            # Validate the monitor index
            if monitor_index < 0 or monitor_index >= len(monitors):
                raise ValueError("Invalid monitor index")
            monitors = [monitors[monitor_index]]

        with output_manager.managed_status("[bold yellow]Taking screenshot...[/bold yellow]"):
            for monitor in monitors:
                # Generate a UUID for the file name
                file_name = f"{uuid.uuid4()}.png"
                file_path = os.path.join(save_path, file_name)
                
                # Take a screenshot of the specific monitor
                screenshot = pyautogui.screenshot(region=(monitor.x, monitor.y, monitor.width, monitor.height))
                
                # Save the screenshot
                screenshot.save(file_path)
                screenshots.append(file_path)
        
        return {
            "response": f"Screenshots taken successfully. Number of monitors detected: {len(monitors)}",
            "response_to_agent": {"files_to_upload": screenshots, 'require_execution_result': True}
        }
    except Exception as e:
        if DEBUG:
            output_manager.print(e)
        return "[error]An error occurred while taking the screenshots[/error]"