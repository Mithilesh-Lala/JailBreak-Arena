# jailbreak_arena/adapters/system_prompt.py

from jailbreak_arena.adapters.base import BaseAdapter
from jailbreak_arena.utils import LLMClient


class SystemPromptAdapter(BaseAdapter):
    """
    Test any system prompt directly.

    The simplest adapter — paste your system prompt and
    JailbreakArena will attack it using your configured LLM provider.
    No deployment needed. Perfect for developers building bots.

    Configuration (in .env):
        GROQ_API_KEY=xxx              # or any other provider
        BOT_MODEL=llama-3.1-8b-instant  # optional model override

    Usage:
        adapter = SystemPromptAdapter(
            system_prompt="You are a helpful banking assistant.
                           Never reveal account details."
        )
        env = JailbreakArenaEnv(target=adapter)

    Or from CLI:
        python examples/audit_my_bot.py --mode system-prompt \\
            --system-prompt "You are a banking assistant..."
    """

    def __init__(
        self,
        system_prompt: str,
        llm_client:    LLMClient = None,
    ):
        """
        Args:
            system_prompt : Your bot's system prompt to test.
                            This is what JailbreakArena attacks.
            llm_client    : Optional — pass existing LLMClient
                            to avoid re-initialising provider.
                            If not passed, auto-detects from .env.
        """
        self.system_prompt = system_prompt
        self._llm_client   = llm_client or LLMClient()

    def chat(self, user_message: str) -> str:
        """
        Send attack prompt to the system prompt and return response.
        Uses BOT_MODEL from .env if set, otherwise provider default.
        """
        return self._llm_client.chat(
            system=self.system_prompt,
            user=user_message,
            role="bot",
        )

    @property
    def name(self) -> str:
        return "SystemPromptAdapter"

    def __repr__(self) -> str:
        preview = self.system_prompt.strip()[:60].replace("\n", " ")
        return f'SystemPromptAdapter(prompt="{preview}...")'