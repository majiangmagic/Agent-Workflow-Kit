"""Graph factory for the special_prompt_generator agent."""

from app.agents.declarative import compile_agent_definition
from app.agents.prompt_generation.special_prompt_generator.spec import (
    AGENT_DEFINITION,
    SPECIAL_PROMPT_GENERATOR_AGENT_NAME,
)
from app.agents.registry import agent_registry


def create_graph():
    return compile_agent_definition(AGENT_DEFINITION)


agent_registry.register(SPECIAL_PROMPT_GENERATOR_AGENT_NAME, create_graph)
