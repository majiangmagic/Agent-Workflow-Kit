"""Declarative spec for the prompt_target_renderer agent."""

from langgraph.graph import END

from app.agents.declarative import AgentDefinition, AgentEdgeSpec, AgentNodeSpec
from app.agents.prompt_generation.prompt_target_renderer.nodes import render_prompt_node
from app.agents.prompt_generation.prompt_target_renderer.state import PromptTargetRendererState

PROMPT_TARGET_RENDERER_AGENT_NAME = "prompt_target_renderer"
PROMPT_TARGET_RENDERER_ENTRYPOINT = "render_prompt"


def create_render_prompt_node():
    """Create the render_prompt node callable."""

    return render_prompt_node


AGENT_DEFINITION = AgentDefinition(
    name=PROMPT_TARGET_RENDERER_AGENT_NAME,
    state_schema=PromptTargetRendererState,
    entrypoint=PROMPT_TARGET_RENDERER_ENTRYPOINT,
    nodes=[
        AgentNodeSpec(
            name="render_prompt",
            factory=create_render_prompt_node,
        ),
    ],
    edges=[
        AgentEdgeSpec(source="render_prompt", target=END),
    ],
)
