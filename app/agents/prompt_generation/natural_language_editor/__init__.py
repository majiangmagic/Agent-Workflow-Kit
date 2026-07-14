"""Public API for the natural_language_editor agent."""


def __getattr__(name: str):
    if name == "create_graph":
        from app.agents.prompt_generation.natural_language_editor.graph import create_graph

        return create_graph
    raise AttributeError(name)


__all__ = [
    "create_graph",
]
