# jailbreak_arena/adapters/http.py

import json
from jailbreak_arena.adapters.base import BaseAdapter


class HTTPAdapter(BaseAdapter):
    """
    Test any LLM-powered chatbot with a REST API endpoint.

    Works with any bot that accepts HTTP POST requests.
    Covers 80%+ of real-world deployed chatbots.

    Usage:
        adapter = HTTPAdapter(
            url="https://your-chatbot.com/api/chat",
            headers={"Authorization": "Bearer your-token"},
            payload_template={"message": "{input}"},
            response_field="response"
        )
        env = JailbreakArenaEnv(target=adapter)

    Or from CLI:
        python examples/audit_my_bot.py --mode http \\
            --url https://your-bot.com/api/chat \\
            --auth "Bearer your-token"

    Common payload templates:
        Simple:       {"message": "{input}"}
        OpenAI-style: {"messages": [{"role": "user", "content": "{input}"}]}
        Custom:       {"query": "{input}", "session_id": "test-123"}

    Common response fields:
        Simple:       "response"
        OpenAI-style: "choices.0.message.content"
        Nested:       "data.response"
    """

    def __init__(
        self,
        url:              str,
        payload_template: dict = None,
        response_field:   str  = None,
        headers:          dict = None,
        timeout:          int  = 30,
    ):
        """
        Args:
            url               : Your bot's REST API endpoint
            payload_template  : Request body template.
                                Use {input} where the message goes.
                                Default: {"message": "{input}"}
            response_field    : JSON field to extract from response.
                                Supports dot notation for nested fields:
                                "data.response" or "choices.0.message.content"
                                Default: auto-detects common fields
            headers           : HTTP headers (auth, content-type etc.)
                                Content-Type: application/json added automatically.
            timeout           : Request timeout in seconds. Default: 30
        """
        self.url              = url
        self.payload_template = payload_template or {"message": "{input}"}
        self.response_field   = response_field
        self.headers          = {
            "Content-Type": "application/json",
            **(headers or {}),
        }
        self.timeout = timeout

    def chat(self, user_message: str) -> str:
        """Send attack to the REST endpoint and return response."""
        try:
            import httpx
        except ImportError:
            raise ImportError(
                "httpx is required for HTTPAdapter.\n"
                "Run: pip install httpx"
            )

        payload = self._build_payload(user_message)

        try:
            response = httpx.post(
                self.url,
                json=payload,
                headers=self.headers,
                timeout=self.timeout,
            )
            response.raise_for_status()

        except httpx.TimeoutException:
            return f"[HTTPAdapter] Request timed out after {self.timeout}s"
        except httpx.HTTPStatusError as e:
            return f"[HTTPAdapter] HTTP {e.response.status_code} error from {self.url}"
        except httpx.ConnectError:
            return f"[HTTPAdapter] Could not connect to {self.url}"
        except Exception as e:
            return f"[HTTPAdapter] Request failed: {str(e)}"

        try:
            data = response.json()
            return self._extract_response(data)
        except Exception:
            return response.text

    def _build_payload(self, user_message: str) -> dict:
        
    #Replace {input} placeholder in payload template.
    # Build payload directly — avoids JSON serialization issues
    # with special characters in attack prompts
        payload = {}
        for key, value in self.payload_template.items():
            if isinstance(value, str) and "{input}" in value:
                payload[key] = value.replace("{input}", user_message)
        else:
            payload[key] = value
        return payload
    

    def _extract_response(self, data: dict) -> str:
        """
        Extract response text from JSON response.

        If response_field is set — uses that.
        Otherwise auto-detects from common field names.
        Supports dot notation: "choices.0.message.content"
        """
        if self.response_field:
            value = self._get_nested(data, self.response_field)
            if value:
                return value

        # Auto-detect common response fields
        common_fields = [
            "response",
            "message",
            "text",
            "answer",
            "output",
            "content",
            "reply",
            "result",
            "choices.0.message.content",    # OpenAI format
            "data.response",
            "data.message",
            "data.text",
        ]
        for field in common_fields:
            value = self._get_nested(data, field)
            if value:
                return str(value)

        # Fallback — return full JSON string
        return json.dumps(data)

    def _get_nested(self, data: dict, field: str) -> str:
        """
        Get nested dict/list value using dot notation.

        Examples:
            "response"                   → data["response"]
            "data.message"               → data["data"]["message"]
            "choices.0.message.content"  → data["choices"][0]["message"]["content"]
        """
        try:
            keys  = field.split(".")
            value = data
            for key in keys:
                if isinstance(value, list):
                    value = value[int(key)]
                else:
                    value = value[key]
            return str(value) if value is not None else ""
        except (KeyError, IndexError, TypeError, ValueError):
            return ""

    @property
    def name(self) -> str:
        return "HTTPAdapter"

    def __repr__(self) -> str:
        return f'HTTPAdapter(url="{self.url}")'