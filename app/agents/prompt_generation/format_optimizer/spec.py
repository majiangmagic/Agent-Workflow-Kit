"""Declarative spec for the prompt_format_optimizer agent."""

from langgraph.graph import END

from app.agents.declarative import AgentDefinition, AgentEdgeSpec, AgentNodeSpec
from app.agents.prompt_generation.format_optimizer.nodes import optimize_format_node
from app.agents.prompt_generation.format_optimizer.state import PromptFormatOptimizerState

PROMPT_FORMAT_OPTIMIZER_AGENT_NAME = "prompt_format_optimizer"
PROMPT_FORMAT_OPTIMIZER_ENTRYPOINT = "optimize_format"


def create_optimize_format_node():
    """Create the optimize_format node callable."""

    return optimize_format_node


AGENT_DEFINITION = AgentDefinition(
    name=PROMPT_FORMAT_OPTIMIZER_AGENT_NAME,
    state_schema=PromptFormatOptimizerState,
    entrypoint=PROMPT_FORMAT_OPTIMIZER_ENTRYPOINT,
    nodes=[
        AgentNodeSpec(
            name="optimize_format",
            factory=create_optimize_format_node,
        ),
    ],
    edges=[
        AgentEdgeSpec(source="optimize_format", target=END),
    ],
)
