"""Declarative spec for the scene_prompt_generator agent."""

from langgraph.graph import END

from app.agents.declarative import AgentDefinition, AgentEdgeSpec, AgentNodeSpec
from app.agents.prompt_generation.scene_prompt_generator.nodes import generate_scene_prompt_node
from app.agents.prompt_generation.scene_prompt_generator.state import ScenePromptGeneratorState

SCENE_PROMPT_GENERATOR_AGENT_NAME = "scene_prompt_generator"
SCENE_PROMPT_GENERATOR_ENTRYPOINT = "generate_scene_prompt"


def create_generate_scene_prompt_node():
    return generate_scene_prompt_node


AGENT_DEFINITION = AgentDefinition(
    name=SCENE_PROMPT_GENERATOR_AGENT_NAME,
    state_schema=ScenePromptGeneratorState,
    entrypoint=SCENE_PROMPT_GENERATOR_ENTRYPOINT,
    nodes=[
        AgentNodeSpec(
            name="generate_scene_prompt",
            factory=create_generate_scene_prompt_node,
        ),
    ],
    edges=[AgentEdgeSpec(source="generate_scene_prompt", target=END)],
)
