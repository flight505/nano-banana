"""
HTTP client using Python stdlib - zero external dependencies.

This module provides a simple HTTP client using urllib.request,
eliminating the need for the 'requests' library and avoiding
PEP 668 dependency installation issues on modern systems.
"""

import json
import urllib.request
import urllib.error
import socket
from typing import Dict, Any, Optional, List


class HttpError(Exception):
    """HTTP error with status code and response body."""

    def __init__(self, status_code: int, body: str):
        self.status_code = status_code
        self.body = body
        try:
            self.json_body = json.loads(body)
        except (json.JSONDecodeError, TypeError):
            self.json_body = None
        super().__init__(f"HTTP {status_code}: {body[:200]}")


class OpenRouterClient:
    """HTTP client for OpenRouter API using Python stdlib.

    Zero external dependencies - uses only urllib.request.
    """

    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, api_key: str, referer: str = "https://github.com/flight505/nano-banana",
                 title: str = "Nano Banana"):
        """
        Initialize the OpenRouter client.

        Args:
            api_key: OpenRouter API key
            referer: HTTP Referer header value
            title: X-Title header value
        """
        self.api_key = api_key
        self.default_headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": referer,
            "X-Title": title,
        }

    def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        modalities: Optional[List[str]] = None,
        timeout: int = 120
    ) -> Dict[str, Any]:
        """
        Make a chat completion request to OpenRouter.

        Args:
            model: Model identifier (e.g., "google/gemini-3-pro-image-preview")
            messages: List of message dictionaries
            modalities: Optional list of modalities (e.g., ["image", "text"])
            timeout: Request timeout in seconds (default: 120)

        Returns:
            API response as dictionary

        Raises:
            HttpError: For HTTP errors (4xx, 5xx)
            ConnectionError: For network errors
            TimeoutError: For timeout errors
        """
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
        }

        if modalities:
            payload["modalities"] = modalities

        return self._post("chat/completions", payload, timeout)

    def _post(self, endpoint: str, payload: Dict[str, Any], timeout: int = 120) -> Dict[str, Any]:
        """
        Make a POST request to the OpenRouter API.

        Args:
            endpoint: API endpoint (e.g., "chat/completions")
            payload: Request payload as dictionary
            timeout: Request timeout in seconds

        Returns:
            Response as dictionary
        """
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=data,
            headers=self.default_headers,
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                response_body = response.read().decode("utf-8")
                try:
                    return json.loads(response_body)
                except json.JSONDecodeError:
                    return {"raw_text": response_body[:500]}

        except urllib.error.HTTPError as e:
            error_body = ""
            try:
                error_body = e.read().decode("utf-8")
            except Exception:
                error_body = str(e)
            raise HttpError(e.code, error_body)

        except urllib.error.URLError as e:
            if isinstance(e.reason, socket.timeout):
                raise TimeoutError(f"Request timed out after {timeout} seconds")
            raise ConnectionError(f"Failed to connect: {e.reason}")

        except socket.timeout:
            raise TimeoutError(f"Request timed out after {timeout} seconds")
