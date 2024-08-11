import pyautogui
import os
import uuid
from screeninfo import get_monitors
from output_manager import OutputManager

output_manager = OutputManager()

DEBUG = os.getenv('DEBUG')

def take_screenshot(monitor_index=None):
    """
    Take a screenshot of one or all monitors and save it to the cache directory. If the users referes to what you see in
    the screen, or say something like "what do you see" in the computer, or screen, use this function.
    Parameters:
    monitor_index (int, optional): The index of the monitor to capture. If not provided, captures all monitors.

    Returns:
    files: The screenshots taken.
    """
    try:
        # Detectar el número de pantallas
        monitors = get_monitors()
        screenshots = []
        save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'cache')
        
        # Check if the save path exists, if not, create it
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        
        if monitor_index is not None:
            # Validar el índice del monitor
            if monitor_index < 0 or monitor_index >= len(monitors):
                raise ValueError("Invalid monitor index")
            monitors = [monitors[monitor_index]]

        with output_manager.managed_status("[bold yellow]Taking screenshot...[/bold yellow]"):
            for monitor in monitors:
                # Generar un UUID para el nombre del archivo
                file_name = f"{uuid.uuid4()}.png"
                file_path = os.path.join(save_path, file_name)
                
                # Tomar una captura de pantalla del monitor específico
                screenshot = pyautogui.screenshot(region=(monitor.x, monitor.y, monitor.width, monitor.height))
                
                # Guardar la captura de pantalla
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