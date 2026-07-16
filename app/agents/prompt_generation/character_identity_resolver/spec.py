"""Declarative spec for the character_identity_resolver agent."""

from langgraph.graph import END

from app.agents.declarative import AgentDefinition, AgentEdgeSpec, AgentNodeSpec
from app.agents.prompt_generation.character_identity_resolver.nodes import resolve_identities_node
from app.agents.prompt_generation.character_identity_resolver.state import CharacterIdentityResolverState

CHARACTER_IDENTITY_RESOLVER_AGENT_NAME = "character_identity_resolver"
CHARACTER_IDENTITY_RESOLVER_ENTRYPOINT = "resolve_identities"


def create_resolve_identities_node():
    """Create the resolve_identities node callable."""

    return resolve_identities_node


AGENT_DEFINITION = AgentDefinition(
    name=CHARACTER_IDENTITY_RESOLVER_AGENT_NAME,
    state_schema=CharacterIdentityResolverState,
    entrypoint=CHARACTER_IDENTITY_RESOLVER_ENTRYPOINT,
    nodes=[
        AgentNodeSpec(
            name="resolve_identities",
            factory=create_resolve_identities_node,
        ),
    ],
    edges=[
        AgentEdgeSpec(source="resolve_identities", target=END),
    ],
)
