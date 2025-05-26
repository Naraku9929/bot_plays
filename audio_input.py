import sounddevice as sd
import wave
import threading
import datetime
import os
import numpy as np # sounddevice often uses numpy arrays for audio data
import time # For example usage

# Installation notes:
# This module requires the following packages:
# pip install sounddevice soundfile numpy
#
# `sounddevice` may also require system-level dependencies such as `portaudio`.
# On Debian/Ubuntu: sudo apt-get install libportaudio2
# On Fedora: sudo dnf install portaudio-devel
# On macOS (using Homebrew): brew install portaudio

class AudioRecorder:
    """
    A class to handle audio recording using sounddevice in a non-blocking way.
    """
    def __init__(self, samplerate=44100, channels=1, dtype='int16'):
        """
        Initializes the AudioRecorder.

        Args:
            samplerate (int): The recording sample rate in Hz.
            channels (int): The number of audio channels.
            dtype (str): The data type for recording (e.g., 'int16', 'float32').
        """
        self.samplerate = samplerate
        self.channels = channels
        self.dtype = dtype
        
        self.is_recording = False
        self.frames = []
        self.stream = None
        self.recording_thread = None
        
        # Check and print available devices if needed for debugging
        # print("Available audio devices:")
        # print(sd.query_devices())
        try:
            sd.check_input_settings(samplerate=self.samplerate, channels=self.channels, dtype=self.dtype)
        except Exception as e:
            print(f"Warning: Preferred input settings might not be supported by any device: {e}")
            print("Attempting to use default device settings if possible.")


    def _callback(self, indata, frames, time, status):
        """
        Callback function for the sounddevice InputStream.
        This function is called by sounddevice for each new block of audio data.
        """
        if status:
            print(f"Audio callback status: {status}") # Print any errors or warnings from the stream
        if self.is_recording:
            self.frames.append(indata.copy())

    def _record_audio(self):
        """
        Private method that runs in a separate thread to manage the audio stream.
        The actual data capture happens in the _callback method.
        This thread keeps the stream alive.
        """
        try:
            # Create and start the input stream
            self.stream = sd.InputStream(
                samplerate=self.samplerate,
                channels=self.channels,
                dtype=self.dtype,
                callback=self._callback
            )
            with self.stream:
                print("Recording thread started, stream opened.")
                # The stream is active and calling _callback.
                # Keep the thread alive while recording.
                while self.is_recording:
                    sd.sleep(100) # Sleep for a short duration to prevent busy-waiting
            print("Stream closed.")
        except Exception as e:
            print(f"Error in recording thread: {e}")
        finally:
            if self.stream and not self.stream.closed:
                self.stream.stop()
                self.stream.close()
            print("Recording thread finished.")

    def start_recording(self):
        """
        Starts the audio recording.
        """
        if self.is_recording:
            print("Already recording.")
            return

        print("Starting recording...")
        self.is_recording = True
        self.frames = [] # Clear previous frames

        # Start the recording in a new thread to keep the main thread non-blocking
        self.recording_thread = threading.Thread(target=self._record_audio)
        self.recording_thread.daemon = True # Allow main program to exit even if thread is running
        self.recording_thread.start()
        print("Recording started.")

    def stop_recording(self, output_directory="recordings"):
        """
        Stops the audio recording and saves it to a WAV file.

        Args:
            output_directory (str): The directory where recordings will be saved.

        Returns:
            str or None: The filepath of the saved recording, or None if saving failed.
        """
        if not self.is_recording:
            print("Not currently recording.")
            return None

        print("Stopping recording...")
        self.is_recording = False # Signal the recording thread and callback to stop

        if self.recording_thread is not None:
            self.recording_thread.join(timeout=5) # Wait for the thread to finish
            if self.recording_thread.is_alive():
                print("Warning: Recording thread did not terminate gracefully.")
            self.recording_thread = None
        
        # Stream should be closed by the _record_audio method's finally block.
        # Ensure it's closed if an error occurred before thread completion.
        if self.stream and not self.stream.closed:
            try:
                self.stream.stop()
                self.stream.close()
                print("Stream stopped and closed in stop_recording as a fallback.")
            except Exception as e:
                print(f"Error stopping/closing stream in stop_recording: {e}")
        self.stream = None


        if not self.frames:
            print("No frames recorded.")
            return None

        # Create the output directory if it doesn't exist
        try:
            os.makedirs(output_directory, exist_ok=True)
        except OSError as e:
            print(f"Error creating output directory '{output_directory}': {e}")
            return None

        # Generate filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recording_{timestamp}.wav"
        filepath = os.path.join(output_directory, filename)

        try:
            print(f"Saving recording to {filepath}...")
            # Concatenate all frames into a single numpy array
            recording_data = np.concatenate(self.frames, axis=0)

            with wave.open(filepath, 'wb') as wf:
                wf.setnchannels(self.channels)
                # Determine sample width from numpy dtype
                # sd.check_dtype(self.dtype) is not standard, use itemsize directly
                sample_width = np.dtype(self.dtype).itemsize 
                wf.setsampwidth(sample_width)
                wf.setframerate(self.samplerate)
                wf.writeframes(recording_data.tobytes())
            
            print(f"Recording saved to {filepath}")
            self.frames = [] # Clear frames after saving
            return filepath
        except Exception as e:
            print(f"Error saving WAV file: {e}")
            return None

if __name__ == '__main__':
    print("AudioRecorder Example Usage:")
    
    # Check for available devices (optional, for debugging)
    try:
        print("Available audio input devices:")
        devices = sd.query_devices()
        input_devices = [device for device in devices if device['max_input_channels'] > 0]
        if not input_devices:
            print("No audio input devices found. This script requires a microphone.")
            # Attempt to proceed, sounddevice might pick a default or fail in start_recording
        else:
            for i, device in enumerate(input_devices):
                print(f"  {i}: {device['name']} (Input Channels: {device['max_input_channels']})")
            # You can set a default device index for sounddevice if needed:
            # sd.default.device = <index_of_your_mic> 
            # Or pass device=<index_or_name> to sd.InputStream
    except Exception as e:
        print(f"Could not query audio devices: {e}. Ensure PortAudio or similar is installed.")
        print("Proceeding with default device settings, which may or may not work.")

    recorder = AudioRecorder(samplerate=44100, channels=1, dtype='int16')
    
    print("\nStarting recording for 5 seconds...")
    recorder.start_recording()
    
    # Record for 5 seconds
    time.sleep(5)
    
    print("\nStopping recording...")
    saved_filepath = recorder.stop_recording(output_directory="my_recordings")
    
    if saved_filepath:
        print(f"Example recording saved at: {saved_filepath}")
    else:
        print("Example recording failed to save.")

    # Example of trying to record again
    print("\nStarting another recording for 3 seconds...")
    recorder.start_recording()
    time.sleep(3)
    print("\nStopping another recording...")
    saved_filepath_2 = recorder.stop_recording(output_directory="my_recordings")

    if saved_filepath_2:
        print(f"Second example recording saved at: {saved_filepath_2}")
    else:
        print("Second example recording failed to save.")
    
    print("\nExample finished.")
