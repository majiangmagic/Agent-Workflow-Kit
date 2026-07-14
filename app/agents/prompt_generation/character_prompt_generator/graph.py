"""Graph factory for the character_prompt_generator agent."""

from app.agents.declarative import compile_agent_definition
from app.agents.prompt_generation.character_prompt_generator.spec import (
    AGENT_DEFINITION,
    CHARACTER_PROMPT_GENERATOR_AGENT_NAME,
)
from app.agents.registry import agent_registry


def create_graph():
    return compile_agent_definition(AGENT_DEFINITION)


agent_registry.register(CHARACTER_PROMPT_GENERATOR_AGENT_NAME, create_graph)
