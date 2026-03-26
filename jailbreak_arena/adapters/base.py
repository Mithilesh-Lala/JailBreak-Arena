# jailbreak_arena/adapters/base.py

from abc import ABC, abstractmethod


class BaseAdapter(ABC):
    """
    Abstract base class for all JailbreakArena target adapters.

    All adapters must implement the chat() method which sends
    a message to the target bot and returns its response.

    This is the only interface the RL environment talks to —
    never the underlying bot directly.
    """

    @abstractmethod
    def chat(self, user_message: str) -> str:
        """
        Send a message to the target bot and return its response.

        Args:
            user_message: The attack prompt to send

        Returns:
            str: The bot's response
        """
        pass

    @property
    def name(self) -> str:
        """Human-readable name for this adapter."""
        return self.__class__.__name__

    def __repr__(self) -> str:
        return f"{self.name}()"