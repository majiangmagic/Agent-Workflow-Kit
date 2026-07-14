"""Business nodes for the scene_prompt_generator agent."""

from typing import Any, Dict

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig

from app.agents.prompt_generation.scene_prompt_generator.state import (
    ScenePromptGeneratorState,
)

DANBOORU_CATEGORY_GENERAL = 0


def generate_scene_prompt_node(
    state: ScenePromptGeneratorState,
    config: RunnableConfig | None = None,
) -> Dict[str, Any]:
    """Use only Danbooru general-category tags for scene/context terms."""

    records = state.get("danbooru_tag_records") or []
    tags = []
    for record in records:
        record_category = record.get("category")
        if record_category is None or int(record_category) != DANBOORU_CATEGORY_GENERAL:
            continue
        name = str(record.get("name") or "").strip()
        if name and name not in tags:
            tags.append(name)

    prompt = ", ".join(tags)
    return {
        "scene_prompt": prompt,
        "scene_tags": tags,
        "messages": [
            AIMessage(
                content=f"Scene/general tags from Danbooru: {len(tags)}.",
                name="scene_prompt_generator",
            )
        ],
    }
