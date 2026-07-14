"""Business nodes for the special_prompt_generator agent."""

from typing import Any, Dict

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig

from app.agents.prompt_generation.special_prompt_generator.state import SpecialPromptGeneratorState


def generate_special_prompt_node(
    state: SpecialPromptGeneratorState,
    config: RunnableConfig | None = None,
) -> Dict[str, Any]:
    """Generate special style/action/composition prompt parts."""

    requirements = state.get("requirements_json") or {}
    style = [str(item) for item in requirements.get("style") or []]
    quality = [str(item) for item in requirements.get("quality") or []]
    special = requirements.get("special") or {}
    if not isinstance(special, dict):
        special = {}
    tags = [str(tag) for tag in special.get("tags") or []]
    prompt = ", ".join([*style, *quality, *tags, "coherent lighting"])
    return {
        "special_prompt": prompt,
        "special_tags": tags,
        "messages": [
            AIMessage(
                content=f"Special prompt prepared: {prompt}",
                name="special_prompt_generator",
            )
        ],
    }
