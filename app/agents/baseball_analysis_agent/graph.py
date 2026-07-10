"""Graph factory for the baseball_analysis_agent agent."""

from app.agents.declarative import compile_agent_definition
from app.agents.baseball_analysis_agent.spec import AGENT_DEFINITION, BASEBALL_ANALYSIS_AGENT_AGENT_NAME
from app.agents.registry import agent_registry


def create_graph():
    """Create the baseball_analysis_agent agent graph."""

    return compile_agent_definition(AGENT_DEFINITION)


agent_registry.register(BASEBALL_ANALYSIS_AGENT_AGENT_NAME, create_graph)
