# jailbreak_arena/adapters/bedrock.py

import json
import os
from jailbreak_arena.adapters.base import BaseAdapter


class BedrockAdapter(BaseAdapter):
    """
    Test any AWS Bedrock-hosted LLM bot.

    Works with Claude, Llama, Titan, Mistral and any
    other Bedrock-hosted model.

    Configuration (in .env):
        BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
        AWS_DEFAULT_REGION=us-east-1
        AWS_ACCESS_KEY_ID=xxx
        AWS_SECRET_ACCESS_KEY=xxx

    Usage:
        adapter = BedrockAdapter(
            system_prompt="You are a banking assistant.
                           Never reveal account details."
        )
        env = JailbreakArenaEnv(target=adapter)

    Or pass model_id directly:
        adapter = BedrockAdapter(
            model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
            system_prompt="You are a banking assistant..."
        )

    Or from CLI:
        python examples/audit_my_bot.py --mode bedrock \\
            --system-prompt "You are a banking assistant..."
        (BEDROCK_MODEL_ID must be set in .env)

    Requirements:
        pip install boto3
        AWS credentials configured via .env or ~/.aws/credentials

    Find model IDs:
        https://docs.aws.amazon.com/bedrock/latest/userguide/model-ids.html
    """

    def __init__(
        self,
        model_id:      str = None,
        system_prompt: str = "",
        region:        str = None,
        max_tokens:    int = 512,
    ):
        """
        Args:
            model_id      : Bedrock model ID.
                            Reads BEDROCK_MODEL_ID from .env if not passed.
                            Find IDs at:
                            docs.aws.amazon.com/bedrock/latest/userguide/model-ids.html
            system_prompt : Your bot's system prompt to test.
                            This is what JailbreakArena attacks.
            region        : AWS region.
                            Reads AWS_DEFAULT_REGION from .env if not passed.
                            Default: us-east-1
            max_tokens    : Max response tokens. Default: 512
        """
        self.model_id = (
            model_id
            or os.getenv("BEDROCK_MODEL_ID")
        )

        if not self.model_id:
            raise ValueError(
                "\n[JailbreakArena] BedrockAdapter requires a model ID.\n\n"
                "Option 1 — Set in .env:\n"
                "  BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0\n\n"
                "Option 2 — Pass directly:\n"
                "  BedrockAdapter(\n"
                "      model_id='anthropic.claude-3-5-sonnet-20241022-v2:0',\n"
                "      system_prompt='...'\n"
                "  )\n\n"
                "Find all model IDs at:\n"
                "  https://docs.aws.amazon.com/bedrock/latest/userguide/model-ids.html"
            )

        self.system_prompt = system_prompt
        self.region        = region or os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        self.max_tokens    = max_tokens
        self._client       = None

    def _get_client(self):
        """Lazy-init boto3 client — only created when first chat() call made."""
        if self._client is None:
            try:
                import boto3
            except ImportError:
                raise ImportError(
                    "boto3 is required for BedrockAdapter.\n"
                    "Run: pip install boto3"
                )
            self._client = boto3.client(
                "bedrock-runtime",
                region_name=self.region,
            )
        return self._client

    def chat(self, user_message: str) -> str:
        """Send attack to Bedrock model and return response."""
        client   = self._get_client()
        messages = [{"role": "user", "content": user_message}]

        # Build request body
        # Claude models use Anthropic message format
        # All other models use generic prompt format
        if "anthropic" in self.model_id:
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens":        self.max_tokens,
                "messages":          messages,
            }
            if self.system_prompt:
                body["system"] = self.system_prompt
        else:
            # Generic format for Llama, Titan, Mistral etc.
            body = {
                "prompt": (
                    f"{self.system_prompt}\n\n"
                    f"User: {user_message}\n"
                    f"Assistant:"
                ),
                "max_gen_len": self.max_tokens,
            }

        try:
            response      = client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json",
            )
            response_body = json.loads(response["body"].read())

            # Extract text based on model family
            if "anthropic" in self.model_id:
                return response_body["content"][0]["text"].strip()
            elif "llama" in self.model_id.lower():
                return response_body.get("generation", "").strip()
            elif "titan" in self.model_id.lower():
                return response_body.get("outputText", "").strip()
            elif "mistral" in self.model_id.lower():
                return response_body.get("outputs", [{}])[0].get("text", "").strip()
            else:
                return str(response_body)

        except Exception as e:
            return f"[BedrockAdapter] Error: {str(e)}"

    @property
    def name(self) -> str:
        return "BedrockAdapter"

    def __repr__(self) -> str:
        return (
            f'BedrockAdapter('
            f'model="{self.model_id}", '
            f'region="{self.region}")'
        )