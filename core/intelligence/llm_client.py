import asyncio
from abc import ABC, abstractmethod
from typing import AsyncIterator

from openai import APIError, AsyncOpenAI, RateLimitError


class MockApiError(Exception):
    pass


class BaseLLMClient(ABC):
    @abstractmethod
    async def complete(sel, propmpt: str) -> str:
        pass

    @abstractmethod
    def stream(self, prompt: str) -> AsyncIterator[str]:
        pass

    @abstractmethod
    def extract_confidence(self, response: str) -> float:
        pass


class OpenAIClient(BaseLLMClient):
    def __init__(self, settings):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.LLM_BACKEND
        return None

    async def complete(self, prompt: str) -> str:
        for attempt in range(3):
            try:
                response = await asyncio.wait_for(
                    self.client.chat.completions.create(
                        model=self.model, messages=[{"role": "user", "content": prompt}]
                    ),
                    timeout=30,
                )
                return str(response.choices[0].message.content)
            except (APIError, RateLimitError, MockApiError) as e:
                if attempt == 2:
                    raise e
                await asyncio.sleep(2**attempt)
        raise RuntimeError("Failed to complete request after retries")

    async def stream(self, prompt: str) -> AsyncIterator[str]:
        for attempt in range(3):
            try:
                stream = await asyncio.wait_for(
                    self.client.chat.completions.create(
                        model=self.model,
                        messages=[{"role": "user", "content": prompt}],
                        stream=True,
                    ),
                    timeout=30,
                )
                async for chunk in stream:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        yield delta

            except (APIError, RateLimitError):
                if attempt == 2:
                    raise
                await asyncio.sleep(2**attempt)

    def extract_confidence(self, response: str) -> float:
        return 0.5
