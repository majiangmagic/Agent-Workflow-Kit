"""Declarative spec for the prompt_aggregator agent."""

from langgraph.graph import END

from app.agents.declarative import AgentDefinition, AgentEdgeSpec, AgentNodeSpec
from app.agents.prompt_generation.prompt_aggregator.nodes import aggregate_prompt_node
from app.agents.prompt_generation.prompt_aggregator.state import PromptAggregatorState

PROMPT_AGGREGATOR_AGENT_NAME = "prompt_aggregator"
PROMPT_AGGREGATOR_ENTRYPOINT = "aggregate_prompt"


def create_aggregate_prompt_node():
    """Create the aggregate_prompt node callable."""

    return aggregate_prompt_node


AGENT_DEFINITION = AgentDefinition(
    name=PROMPT_AGGREGATOR_AGENT_NAME,
    state_schema=PromptAggregatorState,
    entrypoint=PROMPT_AGGREGATOR_ENTRYPOINT,
    nodes=[
        AgentNodeSpec(
            name="aggregate_prompt",
            factory=create_aggregate_prompt_node,
        ),
    ],
    edges=[
        AgentEdgeSpec(source="aggregate_prompt", target=END),
    ],
)
