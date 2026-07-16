"""Public API for the scene_document_editor agent."""


def __getattr__(name: str):
    if name == "create_graph":
        from app.agents.prompt_generation.scene_document_editor.graph import create_graph

        return create_graph
    raise AttributeError(name)


__all__ = [
    "create_graph",
]
