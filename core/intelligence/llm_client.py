import httpx
import json

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Optional

from openai import AsyncOpenAI
from google import genai
from google.genai import types

from core.config import settings
from core.utils.retry import retry

class BaseLLMClient(ABC):
    """BaseLLMClient is an abstract class for other LLMClients."""

    @abstractmethod
    async def complete(self, prompt: str) -> str:
        pass
    
    @abstractmethod
    async def stream(self, prompt: str) -> AsyncIterator[str]:
        pass
    
    @abstractmethod
    def extract_confidence(self, response) -> float:
        pass


class OpenAIClient(BaseLLMClient):
    '''OpenAIClient extended by 'BaseLLMClient'.'''

    def __init__(
            self,
            model: str = "gpt-4o",
            timeout: int = 30,
            **kwargs):
        
        if not self._isValidateFormat(api_key=settings.OPENAI_API_KEY):
            raise ValueError("The provided API key format is invalid")
        
        self.__model = model
        
        try:
            self.__client = AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY,
                timeout=timeout,
                **kwargs
            )
        except Exception as e:
            raise RuntimeError(f"Failed to authenticate: {e}")

    @retry(max_retries=3, base_delay=2)      
    async def complete(self, prompt: str) -> str: 
        messages = [
            {"role": "user", "content": prompt}
        ]
        response = await self.__client.chat.completions.create(
            model = self.__model,
            messages = messages,
        )
        return response.choices[0].message.content
    
    @retry(max_retries=3, base_delay=2)
    async def stream(self, prompt: str) -> AsyncIterator[str]:
        messages = [
            {"role": "user", "content": prompt}
        ]
        stream = await self.__client.chat.completions.create(
            model = self.__model,
            messages = messages,
            stream = True
        )
        
        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content

    def extract_confidence(self, response:str) -> float:
        return 0.5
    
    def _isValidateFormat(self, api_key: str) -> bool:
        '''validate if the key is of OpenAI apikey format'''
        return ( type(api_key)==str and len(api_key)>0 and api_key.startswith("sk-") )
    
class GeminiClient(BaseLLMClient):
    '''GeminiClient extended by 'BaseLLMClient'.'''

    def __init__(
            self,
            model: str = "gemini-1.5-pro",
            timeout: int = 30,
            **kwargs):
        
        if not self._isValidateFormat(api_key=settings.GEMINI_API_KEY):
            raise ValueError("The provided API key format is invalid")
        
        self.__model = model

        try:
            self.__client = genai.Client(
                api_key=settings.GEMINI_API_KEY,
                http_options=types.HttpOptions(timeout=timeout),
                **kwargs
            )
        except Exception as e:
            raise RuntimeError(f"Failed to authenticate: {e}")

    @retry(max_retries=3, base_delay=2)
    async def complete(self, prompt: str) -> types.GenerateContentResponse:
        messages = [
            {"role": "user", "parts": [{"text":prompt}]}
        ]
        response = await self.__client.aio.models.generate_content(
            model=self.__model,
            contents=messages
        )
        return response
    
    @retry(max_retries=3, base_delay=2)
    async def stream(self, prompt: str) -> AsyncIterator[str]:
        messages = [
            {"role": "user", "parts": [{"text":prompt}]}
        ]
        stream = await self.__client.aio.models.generate_content_stream(
            model = self.__model,
            contents = messages
        )

        async for chunk in stream:
            if chunk:
                yield chunk

    def extract_confidence(self, response: types.GenerateContentResponse) -> float:
        score_map = {
            "NEGLIGIBLE": 1.0,
            "LOW": 0.8,
            "MEDIUM": 0.4,
            "HIGH": 0.1,
            "HARM_PROBABILITY_UNSPECIFIED": 0.5
        }
        rating = getattr(response.candidates[0], 'safety_ratings', [])
        if not rating:
            return 0.5
        
        scores = [score_map.get(r.probability, 0.5) for r in rating]
        return min(scores) if scores else 0.5

    def _isValidateFormat(self, api_key: str) -> bool:
        '''validate if the key is of Gemini apikey format'''
        return ( type(api_key)==str and len(api_key)>0 and api_key.startswith('AI') )
    
class LlamaClient(BaseLLMClient):
    '''LlamaClient extended by 'BaseLLMClient'.'''

    def __init__(
        self,
        model: str = "llama3",
        base_url: str = "http://localhost:11434",
        timeout: int = 30
    ):

        self.__model = model
        self.__base_url = base_url
        self.__client = httpx.AsyncClient(timeout=timeout)
    
    @retry(max_retries=3, base_delay=2)
    async def complete(self, prompt: str) -> str:
        payload = {
            "model": self.__model,
            "prompt": prompt,
            "stream": False
        }
        response = await self.__client.post(
            f"{self.__base_url}/api/generate",
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        return data["response"]
    
    @retry(max_retries=3, base_delay=2)
    async def stream(self, prompt: str) -> AsyncIterator[str]:
        payload = {
            "model": self.__model,
            "prompt": prompt,
            "stream": True
        }

        async with self.__client.stream(
            "POST",
            f"{self.__base_url}/api/generate",
            json=payload
        ) as response:
            
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line:
                    continue
                chunk = json.loads(line)
                content = chunk.get("response")
                if content:
                    yield content
                if chunk.get("done"):
                    break

    def extract_confidence(self, response: str) -> float:
        return 0.5          
    
class LLMClientFactory:
    '''LLMClientFactory returns the instance of the llm choosen as backend'''

    @staticmethod
    def create() -> BaseLLMClient:
        backend = settings.LLM_BACKEND.lower()
        if backend == "openai":
            return OpenAIClient()
        elif backend == "gemini":
            return GeminiClient()
        elif backend == "llama":
            return LlamaClient()
        else:
            raise ValueError(f"Unsupported backend: {backend}")
        
class PromptBuilder:
    '''PromptBuilder help guide the user build context aware prompt for LLM for better output'''

    @staticmethod
    def build_guidance_prompt(context, screen_text, trace_summary) -> str:
        return f"""
        You are an intelligent UI guidance assistant.

        Context:
        {context}
        Visible Screen Text:
        {screen_text}
        Previous Interaction Trace:
        {trace_summary}

        Provide the next best action.
        """.strip()
