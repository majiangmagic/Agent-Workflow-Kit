"""Public API for the prompt_format_optimizer agent."""


def __getattr__(name: str):
    if name == "create_graph":
        from app.agents.prompt_generation.format_optimizer.graph import create_graph

        return create_graph
    raise AttributeError(name)


__all__ = [
    "create_graph",
]
