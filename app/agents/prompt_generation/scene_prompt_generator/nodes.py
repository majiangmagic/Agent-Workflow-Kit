"""Business nodes for the scene_prompt_generator agent."""

from typing import Any, Dict

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig

from app.agents.prompt_generation.scene_prompt_generator.state import ScenePromptGeneratorState


def generate_scene_prompt_node(
    state: ScenePromptGeneratorState,
    config: RunnableConfig | None = None,
) -> Dict[str, Any]:
    """Generate the scene-specific prompt part."""

    requirements = state.get("requirements_json") or {}
    scene = requirements.get("scene") or {}
    if not isinstance(scene, dict):
        scene = {}
    tags = [str(tag) for tag in scene.get("tags") or []]
    prompt_parts = [str(value) for value in scene.get("parts") or [] if value]
    if not prompt_parts:
        prompt_parts = ["clear visual scene"]

    prompt = ", ".join([*prompt_parts, *tags])
    return {
        "scene_prompt": prompt,
        "scene_tags": tags,
        "messages": [
            AIMessage(
                content=f"Scene prompt prepared: {prompt}",
                name="scene_prompt_generator",
            )
        ],
    }
