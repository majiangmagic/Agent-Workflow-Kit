"""Business nodes for the prompt_format_converter agent."""

from typing import Any, Dict

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig

from app.agents.prompt_generation.format_converter.state import (
    PromptFormatConverterState,
)


def convert_node(
    state: PromptFormatConverterState,
    config: RunnableConfig | None = None,
) -> Dict[str, Any]:
    """Format the already generated prompt without adding preset prompt terms."""

    draft = str(state.get("draft_prompt") or "")
    negative = str(state.get("negative_prompt") or "")
    target_model = str(state.get("target_model") or "").lower()
    if not target_model:
        requirements = state.get("requirements_json") or {}
        target_model = str(requirements.get("target_model") or "sdxl").lower()

    if target_model == "midjourney":
        formatted = draft
    elif target_model == "flux":
        formatted = draft
    else:
        formatted = (
            f"Positive prompt: {draft}\nNegative prompt: {negative}"
            if negative
            else f"Positive prompt: {draft}"
        )

    final_output = {
        "target_model": target_model,
        "prompt": formatted,
        "negative_prompt": negative,
    }
    return {
        "target_model": target_model,
        "formatted_prompt": formatted,
        "final_output": final_output,
        "messages": [
            AIMessage(
                content=formatted,
                name="prompt_format_converter",
            )
        ],
    }
