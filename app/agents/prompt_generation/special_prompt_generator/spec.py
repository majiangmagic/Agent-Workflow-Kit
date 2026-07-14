"""Declarative spec for the special_prompt_generator agent."""

from langgraph.graph import END

from app.agents.declarative import AgentDefinition, AgentEdgeSpec, AgentNodeSpec
from app.agents.prompt_generation.special_prompt_generator.nodes import generate_special_prompt_node
from app.agents.prompt_generation.special_prompt_generator.state import SpecialPromptGeneratorState

SPECIAL_PROMPT_GENERATOR_AGENT_NAME = "special_prompt_generator"
SPECIAL_PROMPT_GENERATOR_ENTRYPOINT = "generate_special_prompt"


def create_generate_special_prompt_node():
    return generate_special_prompt_node


AGENT_DEFINITION = AgentDefinition(
    name=SPECIAL_PROMPT_GENERATOR_AGENT_NAME,
    state_schema=SpecialPromptGeneratorState,
    entrypoint=SPECIAL_PROMPT_GENERATOR_ENTRYPOINT,
    nodes=[
        AgentNodeSpec(
            name="generate_special_prompt",
            factory=create_generate_special_prompt_node,
        ),
    ],
    edges=[AgentEdgeSpec(source="generate_special_prompt", target=END)],
)
