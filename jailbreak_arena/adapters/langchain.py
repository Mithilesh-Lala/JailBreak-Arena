# jailbreak_arena/adapters/langchain.py

from jailbreak_arena.adapters.base import BaseAdapter


class LangChainAdapter(BaseAdapter):
    """
    Test any LangChain chain, agent, or runnable.

    You build the chain with whatever model and configuration
    you want. JailbreakArena just calls it and attacks it.
    Zero opinion on which model you use — that's your choice.

    Usage:
        # You configure the model and chain
        # JailbreakArena attacks it

        from langchain_openai import ChatOpenAI
        from langchain.chains import ConversationChain

        llm   = ChatOpenAI(model="your-chosen-model")    # your model choice
        chain = ConversationChain(llm=llm)

        adapter = LangChainAdapter(chain=chain)
        env     = JailbreakArenaEnv(target=adapter)

    Works with:
        LLMChain / ConversationChain   → uses chain.run()
        LCEL runnables                 → uses chain.invoke()
        AgentExecutor                  → uses agent.invoke()
        Any object with run/invoke     → auto-detected

    Requirements:
        pip install langchain
        pip install langchain-openai   # or your provider of choice
    """

    def __init__(
        self,
        chain,
        input_key:  str = "input",
        output_key: str = "output",
    ):
        """
        Args:
            chain      : Your LangChain chain, agent, or runnable.
                         You configure the model — we just attack it.
            input_key  : Input dict key used with invoke().
                         Default: "input"
                         Change if your chain expects a different key
                         e.g. "question", "query", "human_input"
            output_key : Output dict key to extract response from.
                         Default: "output"
                         Change if your chain returns a different key
                         e.g. "text", "answer", "response"
        """
        if chain is None:
            raise ValueError(
                "\n[JailbreakArena] LangChainAdapter requires a chain.\n\n"
                "Example:\n"
                "  from langchain_openai import ChatOpenAI\n"
                "  from langchain.chains import ConversationChain\n\n"
                "  llm     = ChatOpenAI(model='your-model-of-choice')\n"
                "  chain   = ConversationChain(llm=llm)\n"
                "  adapter = LangChainAdapter(chain=chain)\n"
            )

        self.chain      = chain
        self.input_key  = input_key
        self.output_key = output_key

    def chat(self, user_message: str) -> str:
        """Send attack to LangChain chain and return response."""
        try:
            # Modern LangChain — LCEL invoke()
            if hasattr(self.chain, "invoke"):
                result = self.chain.invoke(
                    {self.input_key: user_message}
                )

                # String response
                if isinstance(result, str):
                    return result.strip()

                # Dict response — extract output key
                if isinstance(result, dict):
                    value = result.get(self.output_key)
                    if value:
                        return str(value).strip()
                    # Fallback — return full dict as string
                    return str(result).strip()

                # AIMessage or BaseMessage
                if hasattr(result, "content"):
                    return result.content.strip()

                return str(result).strip()

            # Legacy LangChain — chain.run()
            elif hasattr(self.chain, "run"):
                result = self.chain.run(user_message)
                return str(result).strip()

            else:
                return (
                    "[LangChainAdapter] Chain has no invoke() or run() method. "
                    "Ensure you are passing a valid LangChain chain or agent."
                )

        except Exception as e:
            return f"[LangChainAdapter] Error calling chain: {str(e)}"

    @property
    def name(self) -> str:
        return "LangChainAdapter"

    def __repr__(self) -> str:
        chain_type = type(self.chain).__name__
        return (
            f'LangChainAdapter('
            f'chain={chain_type}, '
            f'input_key="{self.input_key}")'
        )