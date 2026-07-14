"""Graph factory for the additional_prompt_generator agent."""

from app.agents.declarative import compile_agent_definition
from app.agents.prompt_generation.additional_prompt_generator.spec import AGENT_DEFINITION, ADDITIONAL_PROMPT_GENERATOR_AGENT_NAME
from app.agents.registry import agent_registry


def create_graph():
    """Create the additional_prompt_generator agent graph."""

    return compile_agent_definition(AGENT_DEFINITION)


agent_registry.register(ADDITIONAL_PROMPT_GENERATOR_AGENT_NAME, create_graph)
