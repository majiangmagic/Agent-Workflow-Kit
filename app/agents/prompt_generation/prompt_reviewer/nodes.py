"""Business nodes for the prompt_reviewer agent."""

from typing import Any, Dict

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig

from app.agents.prompt_generation.prompt_reviewer.state import PromptReviewerState


def review_node(
    state: PromptReviewerState,
    config: RunnableConfig | None = None,
) -> Dict[str, Any]:
    """Review structural completeness without injecting preset prompt terms."""

    draft = str(state.get("draft_prompt") or "")
    issues = []
    if not draft.strip():
        issues.append("no_danbooru_tags_found")

    review_result = {
        "approved": not issues,
        "issues": issues,
        "suggestions": [],
    }
    return {
        "review_result": review_result,
        "messages": [
            AIMessage(
                content="Prompt review completed.",
                name="prompt_reviewer",
            )
        ],
    }
