import mss
from PIL import Image
from typing import Optional, Dict, Any


class ScreenCapture:
    """
    Handles continuous screen capture for digital domain perception.
    Uses 'mss' for high-performance cross-platform screen recording.
    """

    def __init__(self, monitor_index: int = 0):
        self.monitor_index = monitor_index
        self.sct = mss.mss()
        self.is_running = False

    def capture(self) -> Optional[Image.Image]:
        """
        Captures the current screen state and returns it as a PIL Image.
        """
        try:
            # Capture the specified monitor
            monitor = self.sct.monitors[self.monitor_index]
            screenshot = self.sct.grab(monitor)
            
            # Convert to PIL Image
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            return img
        except Exception as e:
            # In a real scenario, we would use the centralized logger here
            print(f"Error capturing screen: {e}")
            return None

    def get_info(self) -> Dict[str, Any]:
        """
        Returns information about the current screen and capture status.
        """
        return {
            "monitor_count": len(self.sct.monitors) - 1,
            "active_monitor": self.monitor_index,
            "is_running": self.is_running
        }
