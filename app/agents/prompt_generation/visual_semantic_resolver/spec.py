"""Declarative spec for the visual_semantic_resolver agent."""

from langgraph.graph import END

from app.agents.declarative import AgentDefinition, AgentEdgeSpec, AgentNodeSpec
from app.agents.prompt_generation.visual_semantic_resolver.nodes import resolve_visual_semantics_node
from app.agents.prompt_generation.visual_semantic_resolver.state import VisualSemanticResolverState

VISUAL_SEMANTIC_RESOLVER_AGENT_NAME = "visual_semantic_resolver"
VISUAL_SEMANTIC_RESOLVER_ENTRYPOINT = "resolve_visual_semantics"


def create_resolve_visual_semantics_node():
    """Create the resolve_visual_semantics node callable."""

    return resolve_visual_semantics_node


AGENT_DEFINITION = AgentDefinition(
    name=VISUAL_SEMANTIC_RESOLVER_AGENT_NAME,
    state_schema=VisualSemanticResolverState,
    entrypoint=VISUAL_SEMANTIC_RESOLVER_ENTRYPOINT,
    nodes=[
        AgentNodeSpec(
            name="resolve_visual_semantics",
            factory=create_resolve_visual_semantics_node,
        ),
    ],
    edges=[
        AgentEdgeSpec(source="resolve_visual_semantics", target=END),
    ],
)
