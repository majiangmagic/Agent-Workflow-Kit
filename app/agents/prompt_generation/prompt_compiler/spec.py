"""Declarative spec for the prompt_compiler agent."""

from langgraph.graph import END

from app.agents.declarative import AgentDefinition, AgentEdgeSpec, AgentNodeSpec
from app.agents.prompt_generation.prompt_compiler.nodes import compile_prompt_node
from app.agents.prompt_generation.prompt_compiler.state import PromptCompilerState

PROMPT_COMPILER_AGENT_NAME = "prompt_compiler"
PROMPT_COMPILER_ENTRYPOINT = "compile_prompt"


def create_compile_prompt_node():
    """Create the compile_prompt node callable."""

    return compile_prompt_node


AGENT_DEFINITION = AgentDefinition(
    name=PROMPT_COMPILER_AGENT_NAME,
    state_schema=PromptCompilerState,
    entrypoint=PROMPT_COMPILER_ENTRYPOINT,
    nodes=[
        AgentNodeSpec(
            name="compile_prompt",
            factory=create_compile_prompt_node,
        ),
    ],
    edges=[
        AgentEdgeSpec(source="compile_prompt", target=END),
    ],
)
