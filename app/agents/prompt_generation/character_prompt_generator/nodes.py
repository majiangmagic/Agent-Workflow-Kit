"""Business nodes for the character_prompt_generator agent."""

from typing import Any, Dict

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig

from app.agents.prompt_generation.character_prompt_generator.state import CharacterPromptGeneratorState


def generate_character_prompt_node(
    state: CharacterPromptGeneratorState,
    config: RunnableConfig | None = None,
) -> Dict[str, Any]:
    """Generate the character-specific prompt part."""

    requirements = state.get("requirements_json") or {}
    characters = requirements.get("characters") or []
    tags: list[str] = []
    names: list[str] = []
    for character in characters:
        if not isinstance(character, dict):
            continue
        name = str(character.get("name") or "").strip()
        if name:
            names.append(name)
        for tag in character.get("tags") or []:
            if tag not in tags:
                tags.append(str(tag))

    if not names:
        raw = str(requirements.get("raw_request") or state.get("user_input") or "")
        names = [raw] if raw else ["main subject"]

    prompt = ", ".join([*names, *tags])
    return {
        "character_prompt": prompt,
        "character_tags": tags,
        "messages": [
            AIMessage(
                content=f"Character prompt prepared: {prompt}",
                name="character_prompt_generator",
            )
        ],
    }
