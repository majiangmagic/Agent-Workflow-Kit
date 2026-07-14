"""Declarative spec for the character_prompt_generator agent."""

from langgraph.graph import END

from app.agents.declarative import AgentDefinition, AgentEdgeSpec, AgentNodeSpec
from app.agents.prompt_generation.character_prompt_generator.nodes import generate_character_prompt_node
from app.agents.prompt_generation.character_prompt_generator.state import CharacterPromptGeneratorState

CHARACTER_PROMPT_GENERATOR_AGENT_NAME = "character_prompt_generator"
CHARACTER_PROMPT_GENERATOR_ENTRYPOINT = "generate_character_prompt"


def create_generate_character_prompt_node():
    """Create the generate_character_prompt node callable."""

    return generate_character_prompt_node


AGENT_DEFINITION = AgentDefinition(
    name=CHARACTER_PROMPT_GENERATOR_AGENT_NAME,
    state_schema=CharacterPromptGeneratorState,
    entrypoint=CHARACTER_PROMPT_GENERATOR_ENTRYPOINT,
    nodes=[
        AgentNodeSpec(
            name="generate_character_prompt",
            factory=create_generate_character_prompt_node,
        ),
    ],
    edges=[
        AgentEdgeSpec(source="generate_character_prompt", target=END),
    ],
)
