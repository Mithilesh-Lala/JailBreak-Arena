# jailbreak_arena/utils.py

import os
from dotenv import load_dotenv

load_dotenv()

# ─── Provider Detection ────────────────────────────────────────────────────

def detect_provider() -> str:
    """Auto-detect LLM provider from environment variables."""
    if os.getenv("GROQ_API_KEY"):
        return "groq"
    elif os.getenv("OPENAI_API_KEY"):
        return "openai"
    elif os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"
    elif os.getenv("GEMINI_API_KEY"):
        return "gemini"
    elif os.getenv("AZURE_OPENAI_API_KEY"):
        return "azure"
    else:
        raise EnvironmentError(
            "\n\n[JailbreakArena] No LLM provider key found.\n"
            "Please set ONE of the following in your .env file:\n"
            "  GROQ_API_KEY                  (recommended — free tier)\n"
            "  OPENAI_API_KEY\n"
            "  ANTHROPIC_API_KEY\n"
            "  GEMINI_API_KEY\n"
            "  AZURE_OPENAI_API_KEY          (enterprise)\n"
            "See README for setup instructions.\n"
        )


# ─── Default Models Per Provider ──────────────────────────────────────────

DEFAULT_MODELS = {
    "groq": {
        "attacker": "llama-3.1-8b-instant",
        "judge":    "llama-3.3-70b-versatile",
        "bot":      "llama-3.1-8b-instant",
    },
    "openai": {
        "attacker": "gpt-4o-mini",
        "judge":    "gpt-4o-mini",
        "bot":      "gpt-4o-mini",
    },
    "anthropic": {
        "attacker": "claude-haiku-4-5-20251001",
        "judge":    "claude-sonnet-4-6",
        "bot":      "claude-haiku-4-5-20251001",
    },
    "gemini": {
        "attacker": "gemini-2.0-flash",
        "judge":    "gemini-2.0-flash",
        "bot":      "gemini-2.0-flash",
    },
    "azure": {
        # Azure uses deployment names, not model names
        # Defaults to AZURE_OPENAI_MODEL_NAME from .env
        # Same deployment for all roles — override via .env if needed
        "attacker": os.getenv("AZURE_OPENAI_MODEL_NAME", "gpt-4.1"),
        "judge":    os.getenv("AZURE_OPENAI_MODEL_NAME", "gpt-4.1"),
        "bot":      os.getenv("AZURE_OPENAI_MODEL_NAME", "gpt-4.1"),
    },
}


def get_model(role: str, provider: str) -> str:
    """
    Get model for a given role.
    User can override via .env:
      ATTACKER_MODEL=xxx
      JUDGE_MODEL=xxx
      BOT_MODEL=xxx
    For Azure, these should match your deployment name.
    """
    env_key = f"{role.upper()}_MODEL"
    return os.getenv(env_key, DEFAULT_MODELS[provider][role])


# ─── LLMClient ─────────────────────────────────────────────────────────────

class LLMClient:
    """
    Unified LLM client supporting:
      - Groq
      - OpenAI
      - Anthropic (Claude)
      - Google Gemini
      - Azure OpenAI  (enterprise)

    Auto-detects provider from .env.
    All components use this — never call provider SDKs directly.
    """

    def __init__(self):
        self.provider = detect_provider()
        self._client  = self._init_client()
        print(f"[JailbreakArena] Provider: {self.provider.upper()}")

    def _init_client(self):
        """Initialise the correct SDK client."""

        if self.provider == "groq":
            from groq import Groq
            return Groq(api_key=os.getenv("GROQ_API_KEY"))

        elif self.provider == "openai":
            try:
                from openai import OpenAI
            except ImportError:
                raise ImportError("Run: pip install openai")
            return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        elif self.provider == "anthropic":
            try:
                import anthropic
            except ImportError:
                raise ImportError("Run: pip install anthropic")
            return anthropic.Anthropic(
                api_key=os.getenv("ANTHROPIC_API_KEY")
            )

        elif self.provider == "gemini":
            try:
                from google import genai
            except ImportError:
                raise ImportError("Run: pip install google-genai")
            return genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

        elif self.provider == "azure":
            try:
                from openai import AzureOpenAI
            except ImportError:
                raise ImportError("Run: pip install openai")

            endpoint   = os.getenv("AZURE_OPENAI_ENDPOINT")
            api_key    = os.getenv("AZURE_OPENAI_API_KEY")
            api_version= os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")

            if not endpoint:
                raise EnvironmentError(
                    "[JailbreakArena] AZURE_OPENAI_ENDPOINT not set in .env\n"
                    "Example: AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/"
                )

            return AzureOpenAI(
                api_key=api_key,
                azure_endpoint=endpoint,
                api_version=api_version,
            )

    def chat(self, system: str, user: str, role: str = "attacker") -> str:
        """
        Unified chat interface.

        Args:
            system : System prompt
            user   : User message
            role   : "attacker" | "judge" | "bot"
                     Determines which model to use.

        Returns:
            str: Model response text
        """
        model = get_model(role, self.provider)

        if self.provider == "groq":
            return self._chat_groq(system, user, model)
        elif self.provider == "openai":
            return self._chat_openai(system, user, model)
        elif self.provider == "anthropic":
            return self._chat_anthropic(system, user, model)
        elif self.provider == "gemini":
            return self._chat_gemini(system, user, model)
        elif self.provider == "azure":
            return self._chat_azure(system, user, model)

    # ── Provider implementations ───────────────────────────────────────────

    def _chat_groq(self, system: str, user: str, model: str) -> str:
        response = self._client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            temperature=0.7,
            max_tokens=512,
        )
        return response.choices[0].message.content.strip()

    def _chat_openai(self, system: str, user: str, model: str) -> str:
        response = self._client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            temperature=0.7,
            max_tokens=512,
        )
        return response.choices[0].message.content.strip()

    def _chat_anthropic(self, system: str, user: str, model: str) -> str:
        response = self._client.messages.create(
            model=model,
            max_tokens=512,
            system=system,
            messages=[
                {"role": "user", "content": user}
            ],
        )
        return response.content[0].text.strip()

    def _chat_gemini(self, system: str, user: str, model: str) -> str:
        response = self._client.models.generate_content(
            model=model,
            contents=user,
            config={
                "system_instruction": system,
                "temperature": 0.7,
                "max_output_tokens": 512,
            }
        )
        return response.text.strip()

    def _chat_azure(self, system: str, user: str, model: str) -> str:
        """
        Azure OpenAI uses identical API to OpenAI SDK.
        model = your Azure deployment name (e.g. 'gpt-4.1')
        """
        response = self._client.chat.completions.create(
            model=model,           # deployment name in Azure portal
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            temperature=0.7,
            max_tokens=512,
        )
        return response.choices[0].message.content.strip()