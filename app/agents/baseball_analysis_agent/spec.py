"""Declarative spec for the baseball_analysis_agent agent."""

from langgraph.graph import END

from app.agents.declarative import AgentDefinition, AgentEdgeSpec, AgentNodeSpec
from app.agents.baseball_analysis_agent.nodes import plan_node, retrieve_node, generate_code_node, execute_code_node, summarize_node
from app.agents.baseball_analysis_agent.state import BaseballAnalysisAgentState

BASEBALL_ANALYSIS_AGENT_AGENT_NAME = "baseball_analysis_agent"
BASEBALL_ANALYSIS_AGENT_ENTRYPOINT = "plan"


def create_plan_node():
    """Create the plan node callable."""

    return plan_node


def create_retrieve_node():
    """Create the retrieve node callable."""

    return retrieve_node


def create_generate_code_node():
    """Create the generate_code node callable."""

    return generate_code_node


def create_execute_code_node():
    """Create the execute_code node callable."""

    return execute_code_node


def create_summarize_node():
    """Create the summarize node callable."""

    return summarize_node


AGENT_DEFINITION = AgentDefinition(
    name=BASEBALL_ANALYSIS_AGENT_AGENT_NAME,
    state_schema=BaseballAnalysisAgentState,
    entrypoint=BASEBALL_ANALYSIS_AGENT_ENTRYPOINT,
    nodes=[
        AgentNodeSpec(
            name="plan",
            factory=create_plan_node,
        ),
        AgentNodeSpec(
            name="retrieve",
            factory=create_retrieve_node,
        ),
        AgentNodeSpec(
            name="generate_code",
            factory=create_generate_code_node,
        ),
        AgentNodeSpec(
            name="execute_code",
            factory=create_execute_code_node,
        ),
        AgentNodeSpec(
            name="summarize",
            factory=create_summarize_node,
        ),
    ],
    edges=[
        AgentEdgeSpec(source="plan", target='retrieve'),
        AgentEdgeSpec(source="retrieve", target='generate_code'),
        AgentEdgeSpec(source="generate_code", target='execute_code'),
        AgentEdgeSpec(source="execute_code", target='summarize'),
        AgentEdgeSpec(source="summarize", target=END),
    ],
)
