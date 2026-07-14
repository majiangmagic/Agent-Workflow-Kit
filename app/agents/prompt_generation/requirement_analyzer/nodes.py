"""Business nodes for the prompt_requirement_analyzer agent."""

from typing import Any, Dict

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig

from app.agents.prompt_generation.requirement_analyzer.state import (
    PromptRequirementAnalyzerState,
)


def analyze_node(
    state: PromptRequirementAnalyzerState,
    config: RunnableConfig | None = None,
) -> Dict[str, Any]:
    """Turn the raw user request into structured prompt requirements."""

    user_input = (state.get("user_input") or "").strip()
    lowered = user_input.lower()
    target_model = "sdxl"
    if "flux" in lowered:
        target_model = "flux"
    elif "midjourney" in lowered or "--" in lowered:
        target_model = "midjourney"
    elif "pony" in lowered:
        target_model = "pony"

    style = []
    for keyword, tag in [
        ("anime", "anime"),
        ("二次元", "anime"),
        ("realistic", "realistic"),
        ("写实", "realistic"),
        ("cyber", "cyberpunk"),
        ("赛博", "cyberpunk"),
        ("watercolor", "watercolor"),
        ("水彩", "watercolor"),
        ("oil", "oil painting"),
    ]:
        haystack = lowered if keyword.isascii() else user_input
        if keyword in haystack and tag not in style:
            style.append(tag)

    requirements = {
        "raw_request": user_input,
        "subject": user_input or "an image subject",
        "query_text": user_input,
        "characters": [],
        "scene": {
            "description": user_input,
            "parts": [],
            "tags": [],
        },
        "special": {
            "tags": [],
        },
        "target_model": target_model,
        "style": style or ["illustration"],
        "quality": ["high detail", "clear composition"],
        "constraints": {
            "avoid": ["low quality", "blurry", "bad anatomy"],
            "language": "english_prompt",
        },
    }
    return {
        "requirements_json": requirements,
        "messages": [
            AIMessage(
                content=f"Requirements JSON prepared for {target_model}.",
                name="prompt_requirement_analyzer",
            )
        ],
    }
