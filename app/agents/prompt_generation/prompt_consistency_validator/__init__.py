"""Public API for the prompt_consistency_validator agent."""


def __getattr__(name: str):
    if name == "create_graph":
        from app.agents.prompt_generation.prompt_consistency_validator.graph import create_graph

        return create_graph
    raise AttributeError(name)


__all__ = [
    "create_graph",
]
