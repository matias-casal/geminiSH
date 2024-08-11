import sounddevice as sd
import soundfile as sf
import queue
import tempfile
import os
from rich.console import Console
import uuid
from pydub import AudioSegment  # Import pydub

console = Console()

DEBUG = os.getenv('DEBUG')

def record(device_index: int = 0):
    """
    Record audio from the computer microphone.
    If the users want to record an audio or talk to you, execute this function.
    If you dont specify the device_index, it will record from the default device.
    
    Parameters:
    device_index (int): The index of the device to record from.

    Returns:
    file: The audio file.
    """
    def callback(indata, frames, time, status):
        q.put(indata.copy())

    q = queue.Queue()
    try:
        device_info = sd.query_devices(kind='input')
        samplerate = int(device_info['default_samplerate'])
        channels = device_info['max_input_channels']
        
        if channels < 1:
            raise ValueError("The selected device has no input channels available.")

        save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../cache')

        if not os.path.exists(save_path):
            os.makedirs(save_path)

        filename = tempfile.mktemp(prefix=f'rec_{uuid.uuid4()}', suffix='.wav', dir=save_path)
        
        with sf.SoundFile(filename, mode='x', samplerate=samplerate, channels=channels) as file:
            with sd.InputStream(samplerate=samplerate, channels=channels, callback=callback):
                with console.status("Recording..."):    
                    while True:
                        file.write(q.get())
                        
    except KeyboardInterrupt:
        # Convert WAV to MP3
        audio = AudioSegment.from_wav(filename)
        mp3_filename = filename.replace('.wav', '.mp3')
        audio.export(mp3_filename, format='mp3')
        os.remove(filename)  # Remove the original WAV file

        return {
            "response": "The recording is ready, follow the user instructions.",
            "response_to_agent": {"files_to_upload": [mp3_filename], 'require_execution_result': True}
        }

    except Exception as e:
        if DEBUG:
            console.print(f"[bold red]{type(e).__name__}: {str(e)}[/bold red]")
        return "[error]An error occurred while recording audio[/error]"