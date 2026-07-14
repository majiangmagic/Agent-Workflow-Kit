"""Declarative spec for the additional_prompt_generator agent."""

from langgraph.graph import END

from app.agents.declarative import AgentDefinition, AgentEdgeSpec, AgentNodeSpec
from app.agents.prompt_generation.additional_prompt_generator.nodes import generate_additional_prompt_node
from app.agents.prompt_generation.additional_prompt_generator.state import AdditionalPromptGeneratorState

ADDITIONAL_PROMPT_GENERATOR_AGENT_NAME = "additional_prompt_generator"
ADDITIONAL_PROMPT_GENERATOR_ENTRYPOINT = "generate_additional_prompt"


def create_generate_additional_prompt_node():
    """Create the generate_additional_prompt node callable."""

    return generate_additional_prompt_node


AGENT_DEFINITION = AgentDefinition(
    name=ADDITIONAL_PROMPT_GENERATOR_AGENT_NAME,
    state_schema=AdditionalPromptGeneratorState,
    entrypoint=ADDITIONAL_PROMPT_GENERATOR_ENTRYPOINT,
    nodes=[
        AgentNodeSpec(
            name="generate_additional_prompt",
            factory=create_generate_additional_prompt_node,
        ),
    ],
    edges=[
        AgentEdgeSpec(source="generate_additional_prompt", target=END),
    ],
)
