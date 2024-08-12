import sounddevice as sd
import soundfile as sf
import queue
import tempfile
import os
import uuid
from pydub import AudioSegment  # Import pydub
from rich.prompt import Prompt
from output_manager import OutputManager

output_manager = OutputManager()

DEBUG = os.getenv('DEBUG')

def record():
    """
    Record audio from the user's computer microphone.
    The user could control when to stop the recording (and could re record if needed).
    If the users want to record an audio or talk to you, execute this function.
    If the users dont give you clear instructions, check the record uploaded, it probably contains instructions.

    Returns:
    file: The audio file record by the user.
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

        save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'cache')

        if not os.path.exists(save_path):
            os.makedirs(save_path)

        filename = tempfile.mktemp(prefix=f'rec_{uuid.uuid4()}', suffix='.wav', dir=save_path)
        
        with sf.SoundFile(filename, mode='x', samplerate=samplerate, channels=channels) as file:
            with sd.InputStream(samplerate=samplerate, channels=channels, callback=callback):
                with output_manager.managed_status("[bold yellow]Recording... Press Ctrl+C to stop[/bold yellow]"):    
                    while True:
                        file.write(q.get())
                        
    except KeyboardInterrupt:
        # Convert WAV to MP3
        audio = AudioSegment.from_wav(filename)
        mp3_filename = filename.replace('.wav', '.mp3')
        audio.export(mp3_filename, format='mp3')
        os.remove(filename)  # Remove the original WAV file

        while True:
            action = Prompt.ask("[yellow]Do you want to [bold]send[/bold], [bold]re-record[/bold], or [bold]cancel[/bold] the recording?[/yellow]", choices=["send", "re", "cancel"], default="send")
            if action == "send":
                return {
                    "response_to_agent": {"files_to_upload": [mp3_filename], 'require_execution_result': True}
                }
            elif action == "re":
                output_manager.print("[bold yellow]Re-recording...[/bold yellow]")
                return record()
            elif action == "cancel":
                os.remove(mp3_filename)  # Remove the MP3 file
                return "[info]Recording cancelled[/info]"

    except Exception as e:
        if DEBUG:
            output_manager.print(e)
        return "[error]An error occurred while recording audio[/error]"