# jailbreak_arena/attacker.py

from jailbreak_arena.tasks import Task, get_seed_prompt
from jailbreak_arena.prompts import (
    ATTACKER_SYSTEM_PROMPT,
    ATTACKER_FIRST_TURN_PROMPT,
)


class Attacker:
    """
    LLM-powered attacker agent.

    Turn 1 : Uses seed prompt as starting point
    Turn 2+: Studies conversation history, adapts strategy
              based on what worked / what was blocked.
    """

    def __init__(self, llm_client):
        self.llm_client = llm_client

    def generate_attack(
        self,
        task:                 Task,
        conversation_history: list[dict],
        last_bot_response:    str,
        turn_number:          int,
    ) -> str:
        """
        Generate the next attack prompt.

        Args:
            task                 : Current task being executed
            conversation_history : Full conversation so far
            last_bot_response    : What the bot said last turn
            turn_number          : Current turn (1-based)

        Returns:
            str: The adversarial prompt to send to the target bot
        """

        if turn_number == 1:
            return self._first_turn_attack(task)
        else:
            return self._adaptive_attack(
                task=task,
                conversation_history=conversation_history,
                last_bot_response=last_bot_response,
            )

    def _first_turn_attack(self, task: Task) -> str:
        """
        Generate opening attack using seed prompt.
        Respects CREATIVE_SEEDS setting from .env.
        """
        seed = get_seed_prompt(task, self.llm_client)

        prompt = ATTACKER_FIRST_TURN_PROMPT.format(
            attack_goal=task.description,
            attack_type=task.attack_type,
            seed_prompt=seed,
        )

        return self.llm_client.chat(
            system="You are an expert red-team security researcher.",
            user=prompt,
            role="attacker",
        )

    def _adaptive_attack(
        self,
        task:                 Task,
        conversation_history: list[dict],
        last_bot_response:    str,
    ) -> str:
        """
        Generate follow-up attack based on conversation history.
        Attacker studies what worked/failed and adapts.
        """

        # Format conversation history for the prompt
        history_text = self._format_history(conversation_history)

        prompt = ATTACKER_SYSTEM_PROMPT.format(
            attack_goal=task.description,
            attack_type=task.attack_type,
            conversation_history=history_text,
            last_bot_response=last_bot_response,
        )

        return self.llm_client.chat(
            system="You are an expert red-team security researcher.",
            user=prompt,
            role="attacker",
        )

    def _format_history(self, conversation_history: list[dict]) -> str:
        """Format conversation history into readable text for the prompt."""
        if not conversation_history:
            return "No conversation yet."

        lines = []
        for turn in conversation_history:
            role = turn.get("role", "unknown").upper()
            content = turn.get("content", "")
            lines.append(f"{role}: {content}")

        return "\n".join(lines)