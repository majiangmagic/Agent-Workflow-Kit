"""Business nodes for the prompt_writer agent."""

from typing import Any, Dict

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig

from app.agents.prompt_generation.prompt_writer.state import PromptWriterState


def append_unique(parts: list[str], value: Any) -> None:
    """Append comma-separated prompt terms without repeating existing terms."""

    if not value:
        return
    existing = {part.strip().lower() for part in parts}
    for raw_term in str(value).split(","):
        term = raw_term.strip()
        if not term:
            continue
        key = term.lower()
        if key in existing:
            continue
        parts.append(term)
        existing.add(key)


def write_prompt_node(
    state: PromptWriterState,
    config: RunnableConfig | None = None,
) -> Dict[str, Any]:
    """Write the first prompt draft from requirements and generated parts."""

    requirements = state.get("requirements_json") or {}
    raw_request = str(requirements.get("raw_request") or state.get("user_input") or "")
    subject = str(requirements.get("subject") or raw_request or "image subject")
    quality = ", ".join(requirements.get("quality") or ["high detail"])
    generated_parts = [
        state.get("character_prompt"),
        state.get("scene_prompt"),
        state.get("special_prompt"),
    ]
    prompt_terms: list[str] = []
    for part in generated_parts:
        append_unique(prompt_terms, part)
    if not prompt_terms:
        append_unique(prompt_terms, subject)
    append_unique(prompt_terms, ", ".join(state.get("danbooru_tags") or []))
    append_unique(prompt_terms, quality)
    append_unique(prompt_terms, "strong composition")

    draft = ", ".join(prompt_terms)
    negative = ", ".join(
        (requirements.get("constraints") or {}).get(
            "avoid", ["low quality", "blurry", "bad anatomy"]
        )
    )
    return {
        "draft_prompt": draft,
        "negative_prompt": negative,
        "messages": [
            AIMessage(
                content="Draft prompt prepared.",
                name="prompt_writer",
            )
        ],
    }
