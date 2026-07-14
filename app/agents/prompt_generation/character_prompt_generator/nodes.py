"""Business nodes for the character_prompt_generator agent."""

from typing import Any, Dict

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig

from app.agents.prompt_generation.character_prompt_generator.state import (
    CharacterPromptGeneratorState,
)

DANBOORU_CATEGORY_CHARACTER = 4


def tag_names_by_category(records: list[dict[str, Any]], category: int) -> list[str]:
    names = []
    for record in records:
        record_category = record.get("category")
        if record_category is None or int(record_category) != category:
            continue
        name = str(record.get("name") or "").strip()
        if name and name not in names:
            names.append(name)
    return names


def generate_character_prompt_node(
    state: CharacterPromptGeneratorState,
    config: RunnableConfig | None = None,
) -> Dict[str, Any]:
    """Use only Danbooru character-category tags."""

    records = state.get("danbooru_tag_records") or []
    tags = tag_names_by_category(records, DANBOORU_CATEGORY_CHARACTER)
    prompt = ", ".join(tags)
    return {
        "character_prompt": prompt,
        "character_tags": tags,
        "messages": [
            AIMessage(
                content=f"Character tags from Danbooru: {len(tags)}.",
                name="character_prompt_generator",
            )
        ],
    }
