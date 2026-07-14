"""Graph factory for the natural_language_editor agent."""

from app.agents.declarative import compile_agent_definition
from app.agents.prompt_generation.natural_language_editor.spec import AGENT_DEFINITION, NATURAL_LANGUAGE_EDITOR_AGENT_NAME
from app.agents.registry import agent_registry


def create_graph():
    """Create the natural_language_editor agent graph."""

    return compile_agent_definition(AGENT_DEFINITION)


agent_registry.register(NATURAL_LANGUAGE_EDITOR_AGENT_NAME, create_graph)
