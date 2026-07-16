"""Declarative spec for the prompt_semantic_repairer agent."""

from langgraph.graph import END

from app.agents.declarative import AgentDefinition, AgentEdgeSpec, AgentNodeSpec
from app.agents.prompt_generation.prompt_semantic_repairer.nodes import repair_semantics_node
from app.agents.prompt_generation.prompt_semantic_repairer.state import PromptSemanticRepairerState

PROMPT_SEMANTIC_REPAIRER_AGENT_NAME = "prompt_semantic_repairer"
PROMPT_SEMANTIC_REPAIRER_ENTRYPOINT = "repair_semantics"


def create_repair_semantics_node():
    """Create the repair_semantics node callable."""

    return repair_semantics_node


AGENT_DEFINITION = AgentDefinition(
    name=PROMPT_SEMANTIC_REPAIRER_AGENT_NAME,
    state_schema=PromptSemanticRepairerState,
    entrypoint=PROMPT_SEMANTIC_REPAIRER_ENTRYPOINT,
    nodes=[
        AgentNodeSpec(
            name="repair_semantics",
            factory=create_repair_semantics_node,
        ),
    ],
    edges=[
        AgentEdgeSpec(source="repair_semantics", target=END),
    ],
)
