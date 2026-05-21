import json
import httpx
import websockets
from typing import List, Optional, AsyncIterator, Callable, Union
from urllib.parse import urlparse, urlunparse
from pydantic import ValidationError
from unittest.mock import MagicMock
from unittest.mock import MagicMock

from .exceptions import ExecraError, ExecraConnectionError, ExecraAuthError
from .models import (
    GuidanceInstruction,
    AskResponse,
    StatusResponse,
    ModeResponse,
    ActionRecord
)
from ._constants import (
    DEFAULT_HOST,
    API_PREFIX,
    WS_GUIDANCE_PATH,
    DEFAULT_TIMEOUT,
    DEFAULT_ACTION_LIMIT,
    MAX_WS_FRAME_SIZE,
    MAX_QUESTION_LENGTH,
    VALID_MODES
)

class ExecraClient:
    """
    The main client for interacting with Execra's API.
    """
    def __init__(self, host: Optional[str] = None, api_key: Optional[Union[str, Callable[[], str]]] = None):
        self._host: Optional[str] = host.rstrip("/") if host else None
        self._api_key_provider = api_key
        self._client: Optional[httpx.AsyncClient] = None
        self._auth_headers: dict = {}

    def __repr__(self):
        connected = self._client is not None
        return f"<ExecraClient host={self._host!r} connected={connected}>"

    def connect(self, host: Optional[str] = None, api_key: Optional[Union[str, Callable[[], str]]] = None) -> None:
        """
        Initializes the connection parameters and the internal HTTP client.
        Raises ExecraError if already connected.
        """
        if self._client is not None:
            raise ExecraError("Already connected. Call close() before reconnecting.")

        if host:
            self._host = host.rstrip("/")
        if api_key:
            self._api_key_provider = api_key

        if self._host is None:
            self._host = DEFAULT_HOST.rstrip("/")

        # Resolve API key
        key = self._api_key_provider() if callable(self._api_key_provider) else self._api_key_provider
        if key:
            self._auth_headers = {"Authorization": f"Bearer {key}"}
        else:
            self._auth_headers = {}
        
        self._client = httpx.AsyncClient(
            base_url=self._host,
            headers=self._auth_headers,
            timeout=DEFAULT_TIMEOUT
        )

    async def close(self) -> None:
        """
        Closes the underlying HTTP client safely.
        """
        if self._client:
            try:
                await self._client.aclose()
            finally:
                self._client = None

    async def __aenter__(self) -> "ExecraClient":
        # If host was provided in __init__, we can auto-connect
        if self._host and self._client is None:
            self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    def _ensure_connected(self) -> None:
        if self._client is None:
            raise ExecraConnectionError("Client is not connected. Call connect() first.")

    def _get_ws_url(self) -> str:
        parsed = urlparse(self._host)
        scheme = "wss" if parsed.scheme == "https" else "ws"
        return urlunparse(parsed._replace(scheme=scheme)) + WS_GUIDANCE_PATH

    async def ask(self, question: str) -> AskResponse:
        """
        Sends a question to the guidance engine and returns an instruction.
        """
        self._ensure_connected()
        
        if len(question) > MAX_QUESTION_LENGTH:
            raise ValueError(f"Question exceeds maximum length of {MAX_QUESTION_LENGTH}")

        try:
            response = await self._client.post(
                f"{API_PREFIX}/guidance/ask",
                json={"question": question}
            )
            self._handle_response_errors(response)
            return AskResponse(**response.json())
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            raise ExecraConnectionError(f"Failed to connect to Execra: {e}")

    async def get_status(self) -> StatusResponse:
        """
        Retrieves the current status of the Execra instance.
        """
        self._ensure_connected()
        try:
            response = await self._client.get(f"{API_PREFIX}/status")
            self._handle_response_errors(response)
            return StatusResponse(**response.json())
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            raise ExecraConnectionError(f"Failed to connect to Execra: {e}")

    async def switch_mode(self, mode: str) -> ModeResponse:
        """
        Switches the execution mode.
        """
        self._ensure_connected()
        
        if mode not in VALID_MODES:
            raise ValueError(f"Invalid mode '{mode}'. Must be one of {VALID_MODES}")

        try:
            response = await self._client.put(
                f"{API_PREFIX}/mode",
                json={"mode": mode}
            )
            self._handle_response_errors(response)
            return ModeResponse(**response.json())
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            raise ExecraConnectionError(f"Failed to connect to Execra: {e}")

    async def get_actions(self, limit: int = DEFAULT_ACTION_LIMIT, offset: int = 0) -> List[ActionRecord]:
        """
        Fetches the history of actions.
        """
        self._ensure_connected()
        try:
            response = await self._client.get(
                f"{API_PREFIX}/actions",
                params={"limit": limit, "offset": offset}
            )
            self._handle_response_errors(response)
            return [ActionRecord(**item) for item in response.json()]
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            raise ExecraConnectionError(f"Failed to connect to Execra: {e}")

    async def stream_guidance(self) -> AsyncIterator[GuidanceInstruction]:
        """
        Opens a WebSocket connection and yields guidance instructions as they arrive.
        """
        self._ensure_connected()
        ws_url = self._get_ws_url()
        
        try:
            async with websockets.connect(ws_url, extra_headers=self._auth_headers) as ws:
                async for raw in ws:
                    if len(raw) > MAX_WS_FRAME_SIZE:
                        raise ExecraError(f"WebSocket frame exceeds size limit of {MAX_WS_FRAME_SIZE} bytes")
                    
                    try:
                        data = json.loads(raw)
                        if data.get("event") == "guidance":
                            payload = data.get("payload")
                            if payload is None:
                                raise ExecraError("WebSocket message missing 'payload' key")
                            yield GuidanceInstruction(**payload)
                    except (json.JSONDecodeError, ValidationError) as e:
                        raise ExecraError(f"Malformed guidance message: {e}")
                    
        except Exception as e:
            # Re-wrap known connection errors
            is_ws_close = (
                "ConnectionClosed" in type(e).__name__ or 
                (hasattr(websockets, "ConnectionClosed") and isinstance(e, websockets.ConnectionClosed))
            )
            if is_ws_close:
                raise ExecraConnectionError(f"WebSocket connection closed: {e}")
                
            if isinstance(e, (websockets.InvalidHandshake, getattr(websockets, "exceptions", MagicMock()).InvalidHandshake)):
                if "401" in str(e) or "403" in str(e):
                    raise ExecraAuthError(f"WebSocket authentication failed: {e}")
                raise ExecraConnectionError(f"WebSocket handshake failed: {e}")
            
            if isinstance(e, ExecraError):
                raise e
                
            raise ExecraError(f"An error occurred during streaming: {type(e).__name__}: {e}")

    def _handle_response_errors(self, response: httpx.Response) -> None:
        # Truncate body to prevent leaking massive stack traces or sensitive data
        body = response.text[:500] if response.text else "<empty>"
        
        if response.status_code in (401, 403):
            raise ExecraAuthError(
                f"Authentication failed: {body}",
                status_code=response.status_code
            )
        elif 400 <= response.status_code < 600:
            raise ExecraError(
                f"API error ({response.status_code}): {body}",
                status_code=response.status_code
            )
