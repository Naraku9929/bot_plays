import mss
import mss.tools
import datetime
import os
import time # For example usage

# Installation notes:
# This module requires the 'mss' package for screen capture.
# Install it using pip:
# pip install mss
#
# `mss` might also require system-level dependencies for interacting with the display server.
# On Linux, this often includes X11 libraries like `libxrandr-dev`, `libxinerama-dev`, `libxfixes-dev`.
# e.g., sudo apt-get install libxrandr-dev libxinerama-dev libxfixes-dev (Debian/Ubuntu)

class ScreenCapture:
    """
    A class to handle screen capture functionality using the mss library.
    """
    def __init__(self):
        """
        Initializes the ScreenCapture class.
        Currently, no specific initialization parameters are needed.
        """
        pass

    def capture_screen(self, output_directory="screenshots", filename=None):
        """
        Captures the primary screen and saves it to a PNG file.

        Args:
            output_directory (str): The directory where the screenshot will be saved.
                                    Defaults to "screenshots".
            filename (str, optional): The desired filename for the screenshot.
                                      If None, a timestamped filename will be generated.
                                      Must end with '.png'. Defaults to None.

        Returns:
            str or None: The full filepath of the saved screenshot, or None if capture failed.
        """
        try:
            # Create the output directory if it doesn't exist
            os.makedirs(output_directory, exist_ok=True)
        except OSError as e:
            print(f"Error creating output directory '{output_directory}': {e}")
            return None

        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
        elif not filename.lower().endswith(".png"):
            # Ensure the filename has a .png extension if provided
            print(f"Warning: Provided filename '{filename}' does not end with .png. Appending .png.")
            filename += ".png"
            
        filepath = os.path.join(output_directory, filename)

        try:
            with mss.mss() as sct:
                # sct.monitors[0] is a bounding box of all monitors
                # sct.monitors[1] is the primary monitor
                # sct.monitors[2], etc., are other monitors
                if len(sct.monitors) < 2:
                    print("Error: Primary monitor (monitor 1) not found. Using all monitors (monitor 0).")
                    # Fallback to capturing all monitors if only one entry (all monitors) exists.
                    # This can happen on some systems or if no physical primary is designated.
                    if not sct.monitors:
                        print("Error: No monitors detected by mss.")
                        return None
                    monitor_to_capture = sct.monitors[0]
                else:
                    monitor_to_capture = sct.monitors[1]
                
                # Capture the screen
                sct_img = sct.grab(monitor_to_capture)
                
                # Save to a file
                mss.tools.to_png(sct_img.rgb, sct_img.size, output=filepath)
                
                print(f"Screenshot saved to {filepath}")
                return filepath
        except mss.exception.ScreenShotError as e:
            print(f"MSS ScreenShotError: {e}. This might be due to display server issues (e.g., Wayland without XWayland, or no display server).")
            print("Ensure an X server (like Xvfb or a physical display) is available and configured if running headless.")
            return None
        except Exception as e:
            print(f"An error occurred during screen capture: {e}")
            return None

if __name__ == '__main__':
    print("ScreenCapture Example Usage:")
    
    # Create a ScreenCapture instance
    capturer = ScreenCapture()
    
    # Capture screen with default filename and directory
    print("\nCapturing screen with default settings...")
    filepath1 = capturer.capture_screen()
    if filepath1:
        print(f"Default capture saved to: {filepath1}")
    else:
        print("Default capture failed.")

    # Wait a second to ensure a different timestamp for the next file
    time.sleep(1)

    # Capture screen with a custom filename and directory
    print("\nCapturing screen with custom settings...")
    custom_dir = "custom_screenshots"
    custom_file = "my_special_capture.png"
    filepath2 = capturer.capture_screen(output_directory=custom_dir, filename=custom_file)
    if filepath2:
        print(f"Custom capture saved to: {filepath2}")
    else:
        print("Custom capture failed.")

    # Wait a second
    time.sleep(1)

    # Capture screen with a custom filename that needs .png appended
    print("\nCapturing screen with custom filename (no extension)...")
    filepath3 = capturer.capture_screen(filename="another_capture") # Will append .png
    if filepath3:
        print(f"Capture with auto-appended .png saved to: {filepath3}")
    else:
        print("Capture with auto-appended .png failed.")
        
    print("\nScreenCapture example finished.")
