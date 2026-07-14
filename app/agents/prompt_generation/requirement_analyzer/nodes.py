"""Business nodes for the prompt_requirement_analyzer agent."""

from typing import Any, Dict

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig

from app.agents.prompt_generation.requirement_analyzer.state import PromptRequirementAnalyzerState


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
        ("赛博", "cyberpunk"),
        ("cyber", "cyberpunk"),
        ("水彩", "watercolor"),
        ("oil", "oil painting"),
    ]:
        haystack = lowered if keyword.isascii() else user_input
        if keyword in haystack and tag not in style:
            style.append(tag)

    characters = []
    if "伊蕾娜" in user_input or "elaina" in lowered or "魔女之旅" in user_input:
        characters.append(
            {
                "name": "Elaina",
                "source": "Majo no Tabitabi",
                "tags": [
                    "elaina_(majo_no_tabitabi)",
                    "majo_no_tabitabi",
                    "witch_hat",
                    "grey_hair",
                    "long_hair",
                    "blue_eyes",
                ],
            }
        )

    scene_parts = []
    scene_tags = []
    for keyword, part, tag in [
        ("林", "forest", "forest"),
        ("森林", "forest", "forest"),
        ("树", "trees", "tree"),
        ("飞行", "flying through the air", "flying"),
        ("扫帚", "riding a broom", "broom"),
        ("broom", "riding a broom", "broom"),
        ("city", "city", "city"),
        ("rain", "rain", "rain"),
        ("night", "night", "night"),
        ("城市", "city", "city"),
        ("雨", "rain", "rain"),
        ("夜", "night", "night"),
    ]:
        haystack = lowered if keyword.isascii() else user_input
        if keyword in haystack:
            if part not in scene_parts:
                scene_parts.append(part)
            if tag not in scene_tags:
                scene_tags.append(tag)

    special_tags = []
    for keyword, tag in [
        ("全身", "full_body"),
        ("半身", "upper_body"),
        ("portrait", "portrait"),
        ("动态", "dynamic_pose"),
        ("dynamic", "dynamic_pose"),
    ]:
        haystack = lowered if keyword.isascii() else user_input
        if keyword in haystack and tag not in special_tags:
            special_tags.append(tag)

    requirements = {
        "raw_request": user_input,
        "subject": user_input or "an image subject",
        "characters": characters,
        "scene": {
            "parts": scene_parts,
            "tags": scene_tags,
        },
        "special": {
            "tags": special_tags,
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
