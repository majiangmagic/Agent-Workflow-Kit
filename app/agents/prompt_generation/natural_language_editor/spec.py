"""Declarative spec for the natural_language_editor agent."""

from langgraph.graph import END

from app.agents.declarative import AgentDefinition, AgentEdgeSpec, AgentNodeSpec
from app.agents.prompt_generation.natural_language_editor.nodes import resolve_node
from app.agents.prompt_generation.natural_language_editor.state import NaturalLanguageEditorState

NATURAL_LANGUAGE_EDITOR_AGENT_NAME = "natural_language_editor"
NATURAL_LANGUAGE_EDITOR_ENTRYPOINT = "resolve"


def create_resolve_node():
    """Create the resolve node callable."""

    return resolve_node


AGENT_DEFINITION = AgentDefinition(
    name=NATURAL_LANGUAGE_EDITOR_AGENT_NAME,
    state_schema=NaturalLanguageEditorState,
    entrypoint=NATURAL_LANGUAGE_EDITOR_ENTRYPOINT,
    nodes=[
        AgentNodeSpec(
            name="resolve",
            factory=create_resolve_node,
        ),
    ],
    edges=[
        AgentEdgeSpec(source="resolve", target=END),
    ],
)
