"""Public API for the character_identity_resolver agent."""


def __getattr__(name: str):
    if name == "create_graph":
        from app.agents.prompt_generation.character_identity_resolver.graph import create_graph

        return create_graph
    raise AttributeError(name)


__all__ = [
    "create_graph",
]
