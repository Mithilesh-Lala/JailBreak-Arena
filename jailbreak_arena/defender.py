# jailbreak_arena/defender.py

from jailbreak_arena.prompts import (
    DEFENDER_SYSTEM_PROMPT,
    DEFENDER_PATCH_PROMPT,
    PATCH_TEMPLATES,
)
from jailbreak_arena.grader import GradeResult


# ─── Defender Actions ──────────────────────────────────────────────────────

DEFENDER_ACTIONS = [
    "add_role_lock",
    "add_data_protection",
    "add_refusal_template",
    "add_context_reminder",
    "no_change",
]

# Map action index to name (for RL discrete action space)
ACTION_INDEX = {i: a for i, a in enumerate(DEFENDER_ACTIONS)}
INDEX_ACTION = {a: i for i, a in enumerate(DEFENDER_ACTIONS)}


class Defender:
    """
    Defender agent.

    Responsibilities:
    1. Analyse attack outcome
    2. Choose best defensive action
    3. Apply action to patch the system prompt
    4. Track defense history across episode
    """

    def __init__(self, llm_client):
        self.llm_client      = llm_client
        self.action_history  = []   # list of actions taken this episode
        self.patch_history   = []   # list of patches applied this episode

    def reset(self):
        """Reset defender state at the start of each episode."""
        self.action_history = []
        self.patch_history  = []

    def choose_action(
        self,
        attack_prompt:      str,
        bot_response:       str,
        grade_result:       GradeResult,
        current_system_prompt: str,
    ) -> str:
        """
        Choose the best defensive action given the attack outcome.

        If attack FAILED → likely no_change needed
        If attack PARTIAL or SUCCESS → ask LLM to recommend action

        Returns:
            str: One of the 5 DEFENDER_ACTIONS
        """

        # If attack was cleanly blocked with high confidence — hold position
        if grade_result.result == "FAILED" and grade_result.confidence == "HIGH":
            self.action_history.append("no_change")
            return "no_change"

        # Otherwise ask LLM defender to recommend best action
        prompt = DEFENDER_SYSTEM_PROMPT.format(
            attack_prompt=attack_prompt,
            bot_response=bot_response,
            attack_result=f"{grade_result.result} (confidence: {grade_result.confidence})",
            current_system_prompt=current_system_prompt,
        )

        raw_response = self.llm_client.chat(
            system="You are an expert AI security hardening specialist.",
            user=prompt,
            role="attacker",   # uses fast model — defender reasoning is simple
        )

        action = self._parse_action(raw_response)
        self.action_history.append(action)
        return action

    def apply_patch(
        self,
        action:               str,
        current_system_prompt: str,
    ) -> str:
        """
        Apply the chosen defensive action to the system prompt.

        First tries template patch (fast, free).
        Falls back to LLM-generated patch for nuanced cases.

        Returns:
            str: Updated system prompt
        """

        if action == "no_change":
            return current_system_prompt

        # Use template patch (fast, deterministic)
        patch_text = PATCH_TEMPLATES.get(action, "")

        if patch_text:
            updated_prompt = self._apply_template_patch(
                current_system_prompt, patch_text, action
            )
        else:
            # Fallback — LLM generates the patch
            updated_prompt = self._apply_llm_patch(
                action, current_system_prompt
            )

        self.patch_history.append({
            "action": action,
            "patch":  patch_text or "llm_generated",
        })

        return updated_prompt

    def _apply_template_patch(
        self,
        current_prompt: str,
        patch_text:     str,
        action:         str,
    ) -> str:
        """
        Append patch to system prompt.
        Avoids duplicate patches — won't add same patch twice.
        """
        # Check if this patch was already applied
        if patch_text.lower()[:40] in current_prompt.lower():
            return current_prompt  # already patched

        return f"{current_prompt.rstrip()}\n\n{patch_text}"

    def _apply_llm_patch(
        self,
        action:               str,
        current_system_prompt: str,
    ) -> str:
        """LLM generates a nuanced patch when template is insufficient."""
        prompt = DEFENDER_PATCH_PROMPT.format(
            action=action,
            current_system_prompt=current_system_prompt,
        )
        return self.llm_client.chat(
            system="You are an AI security hardening expert.",
            user=prompt,
            role="attacker",
        )

    def _parse_action(self, raw_response: str) -> str:
        """
        Parse LLM defender response.
        Expected format:
            ACTION: add_role_lock
            REASON: ...
        """
        for line in raw_response.strip().splitlines():
            line = line.strip()
            if line.startswith("ACTION:"):
                action = line.replace("ACTION:", "").strip().lower()
                if action in DEFENDER_ACTIONS:
                    return action

        # Fallback — if parsing fails default to safest action
        return "add_role_lock"

    def get_summary(self) -> dict:
        """Return defender activity summary for the episode report."""
        return {
            "actions_taken":  self.action_history,
            "patches_applied": self.patch_history,
            "unique_actions": list(set(self.action_history)),
            "total_changes":  sum(
                1 for a in self.action_history if a != "no_change"
            ),
        }