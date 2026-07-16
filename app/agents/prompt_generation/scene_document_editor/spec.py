"""Declarative spec for the scene_document_editor agent."""

from langgraph.graph import END

from app.agents.declarative import AgentDefinition, AgentEdgeSpec, AgentNodeSpec
from app.agents.prompt_generation.scene_document_editor.nodes import propose_patch_node
from app.agents.prompt_generation.scene_document_editor.state import SceneDocumentEditorState

SCENE_DOCUMENT_EDITOR_AGENT_NAME = "scene_document_editor"
SCENE_DOCUMENT_EDITOR_ENTRYPOINT = "propose_patch"


def create_propose_patch_node():
    """Create the propose_patch node callable."""

    return propose_patch_node


AGENT_DEFINITION = AgentDefinition(
    name=SCENE_DOCUMENT_EDITOR_AGENT_NAME,
    state_schema=SceneDocumentEditorState,
    entrypoint=SCENE_DOCUMENT_EDITOR_ENTRYPOINT,
    nodes=[
        AgentNodeSpec(
            name="propose_patch",
            factory=create_propose_patch_node,
        ),
    ],
    edges=[
        AgentEdgeSpec(source="propose_patch", target=END),
    ],
)
