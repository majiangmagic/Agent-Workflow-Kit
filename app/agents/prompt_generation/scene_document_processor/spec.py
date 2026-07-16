"""Declarative spec for the scene_document_processor agent."""

from langgraph.graph import END

from app.agents.declarative import AgentDefinition, AgentEdgeSpec, AgentNodeSpec
from app.agents.prompt_generation.scene_document_processor.nodes import apply_patch_node
from app.agents.prompt_generation.scene_document_processor.state import SceneDocumentProcessorState

SCENE_DOCUMENT_PROCESSOR_AGENT_NAME = "scene_document_processor"
SCENE_DOCUMENT_PROCESSOR_ENTRYPOINT = "apply_patch"


def create_apply_patch_node():
    """Create the apply_patch node callable."""

    return apply_patch_node


AGENT_DEFINITION = AgentDefinition(
    name=SCENE_DOCUMENT_PROCESSOR_AGENT_NAME,
    state_schema=SceneDocumentProcessorState,
    entrypoint=SCENE_DOCUMENT_PROCESSOR_ENTRYPOINT,
    nodes=[
        AgentNodeSpec(
            name="apply_patch",
            factory=create_apply_patch_node,
        ),
    ],
    edges=[
        AgentEdgeSpec(source="apply_patch", target=END),
    ],
)
