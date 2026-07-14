"""Special prompt generator agent package."""

__all__ = ["create_graph"]


def __getattr__(name):
    if name == "create_graph":
        from app.agents.prompt_generation.special_prompt_generator.graph import create_graph

        return create_graph
    raise AttributeError(name)
