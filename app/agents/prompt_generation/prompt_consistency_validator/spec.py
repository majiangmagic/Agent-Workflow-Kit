"""Declarative spec for the prompt_consistency_validator agent."""

from langgraph.graph import END

from app.agents.declarative import AgentDefinition, AgentEdgeSpec, AgentNodeSpec
from app.agents.prompt_generation.prompt_consistency_validator.nodes import validate_prompt_node
from app.agents.prompt_generation.prompt_consistency_validator.state import PromptConsistencyValidatorState

PROMPT_CONSISTENCY_VALIDATOR_AGENT_NAME = "prompt_consistency_validator"
PROMPT_CONSISTENCY_VALIDATOR_ENTRYPOINT = "validate_prompt"


def create_validate_prompt_node():
    """Create the validate_prompt node callable."""

    return validate_prompt_node


AGENT_DEFINITION = AgentDefinition(
    name=PROMPT_CONSISTENCY_VALIDATOR_AGENT_NAME,
    state_schema=PromptConsistencyValidatorState,
    entrypoint=PROMPT_CONSISTENCY_VALIDATOR_ENTRYPOINT,
    nodes=[
        AgentNodeSpec(
            name="validate_prompt",
            factory=create_validate_prompt_node,
        ),
    ],
    edges=[
        AgentEdgeSpec(source="validate_prompt", target=END),
    ],
)
