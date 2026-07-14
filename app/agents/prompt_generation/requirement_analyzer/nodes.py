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
    """Keep user requirements structured without injecting local prompt presets."""

    user_input = (state.get("user_input") or "").strip()
    lowered = user_input.lower()
    target_model = "sdxl"
    if "flux" in lowered:
        target_model = "flux"
    elif "midjourney" in lowered or "--" in lowered:
        target_model = "midjourney"
    elif "pony" in lowered:
        target_model = "pony"

    requirements = {
        "raw_request": user_input,
        "query_text": user_input,
        "target_model": target_model,
    }
    return {
        "requirements_json": requirements,
        "messages": [
            AIMessage(
                content=f"Requirements prepared for {target_model}.",
                name="prompt_requirement_analyzer",
            )
        ],
    }
