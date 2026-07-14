"""Business nodes for the prompt_danbooru_query agent."""

from typing import Any, Dict

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig

from app.agents.prompt_generation.danbooru_query.state import PromptDanbooruQueryState


def query_tags_node(
    state: PromptDanbooruQueryState,
    config: RunnableConfig | None = None,
) -> Dict[str, Any]:
    """Map requirements to Danbooru-style tags."""

    requirements = state.get("requirements_json") or {}
    raw_request = str(requirements.get("raw_request") or state.get("user_input") or "")
    lowered = raw_request.lower()
    tags = ["masterpiece", "best_quality"]

    style_tags = {
        "anime": ["anime_style", "detailed_eyes"],
        "realistic": ["realistic", "photorealistic"],
        "cyberpunk": ["cyberpunk", "neon_lights", "cityscape"],
        "watercolor": ["watercolor_(medium)", "soft_colors"],
        "oil painting": ["oil_painting_(medium)", "painterly"],
        "illustration": ["illustration", "detailed"],
    }
    for style in requirements.get("style") or ["illustration"]:
        for tag in style_tags.get(str(style), []):
            if tag not in tags:
                tags.append(tag)

    for character in requirements.get("characters") or []:
        if not isinstance(character, dict):
            continue
        for tag in character.get("tags") or []:
            tag = str(tag)
            if tag not in tags:
                tags.append(tag)

    for section_name in ["scene", "special"]:
        section = requirements.get(section_name) or {}
        if not isinstance(section, dict):
            continue
        for tag in section.get("tags") or []:
            tag = str(tag)
            if tag not in tags:
                tags.append(tag)

    keyword_tags = [
        ("girl", "1girl"),
        ("boy", "1boy"),
        ("cat", "cat"),
        ("dragon", "dragon"),
        ("city", "city"),
        ("rain", "rain"),
        ("night", "night"),
        ("portrait", "portrait"),
        ("伊蕾娜", "elaina_(majo_no_tabitabi)"),
        ("魔女之旅", "majo_no_tabitabi"),
        ("魔女", "witch"),
        ("飞行", "flying"),
        ("扫帚", "broom"),
        ("林", "forest"),
        ("森林", "forest"),
        ("全身", "full_body"),
        ("半身", "upper_body"),
        ("夜", "night"),
        ("雨", "rain"),
        ("城市", "city"),
    ]
    for keyword, tag in keyword_tags:
        haystack = lowered if keyword.isascii() else raw_request
        if keyword in haystack and tag not in tags:
            tags.append(tag)

    return {
        "danbooru_tags": tags,
        "tag_notes": "Local Danbooru-style tag mapping; replace this node to call a real Danbooru API.",
        "messages": [
            AIMessage(
                content=f"Prepared {len(tags)} Danbooru-style tags.",
                name="prompt_danbooru_query",
            )
        ],
    }
