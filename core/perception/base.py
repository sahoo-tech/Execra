from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BasePerceptionEngine(ABC):
    """
    Abstract base class for all perception engines (screen, camera, etc.).
    Defines the standard interface for starting, stopping, and retrieving data.
    """

    def __init__(self, name: str):
        self.name = name
        self.is_running = False

    @abstractmethod
    def start(self) -> bool:
        """
        Starts the perception engine.
        Returns True if successful, False otherwise.
        """
        pass

    @abstractmethod
    def stop(self) -> bool:
        """
        Stops the perception engine.
        Returns True if successful, False otherwise.
        """
        pass

    @abstractmethod
    def get_data(self) -> Dict[str, Any]:
        """
        Retrieves the latest captured data from the engine.
        Should return a dictionary containing the processed information.
        """
        pass

    def get_status(self) -> Dict[str, Any]:
        """
        Returns the current status of the engine.
        """
        return {
            "name": self.name,
            "is_running": self.is_running
        }
