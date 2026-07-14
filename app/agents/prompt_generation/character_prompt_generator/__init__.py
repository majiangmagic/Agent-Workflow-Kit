"""Public API for the character_prompt_generator agent."""


def __getattr__(name: str):
    if name == "create_graph":
        from app.agents.prompt_generation.character_prompt_generator.graph import create_graph

        return create_graph
    raise AttributeError(name)


__all__ = [
    "create_graph",
]
