"""Business nodes for the special_prompt_generator agent."""

from typing import Any, Dict

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig

from app.agents.prompt_generation.special_prompt_generator.state import (
    SpecialPromptGeneratorState,
)


def generate_special_prompt_node(
    state: SpecialPromptGeneratorState,
    config: RunnableConfig | None = None,
) -> Dict[str, Any]:
    """Do not invent special prompt terms without an external source."""

    return {
        "special_prompt": "",
        "special_tags": [],
        "messages": [
            AIMessage(
                content="No special tags added without Danbooru-backed evidence.",
                name="special_prompt_generator",
            )
        ],
    }
