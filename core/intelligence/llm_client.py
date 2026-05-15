from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseLLMClient(ABC):
    """
    Abstract base class for all LLM clients (OpenAI, Gemini, etc.).
    Provides a unified interface for the intelligence layer.
    """

    def __init__(self, model_name: str, api_key: str):
        self.model_name = model_name
        self.api_key = api_key

    @abstractmethod
    async def generate_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """
        Generates a text response from the LLM based on the prompt.
        """
        pass

    @abstractmethod
    async def get_embedding(self, text: str) -> List[float]:
        """
        Generates an embedding vector for the given text.
        """
        pass

    def get_info(self) -> Dict[str, str]:
        """
        Returns basic information about the client.
        """
        return {
            "model": self.model_name,
            "provider": self.__class__.__name__.replace("Client", "")
        }
