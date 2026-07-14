"""State schema for the prompt_format_optimizer agent."""

from typing import Any, Dict, List, Optional, TypedDict

from langchain_core.messages import BaseMessage


class PromptFormatOptimizerState(TypedDict):
    """Runtime state for this generated agent."""

    agent_id: str
    agent_name: str
    description: Optional[str]
    system_prompt: Optional[str]
    model: Optional[str]
    temperature: float
    tools: List[Dict[str, Any]]
    messages: List[BaseMessage]
    user_input: Optional[str]

    # 下面是 DSL 声明的业务状态字段。
    requirements_json: Optional[Dict[str, Any]]
    draft_prompt: Optional[str]
    negative_prompt: Optional[str]
    prompt_sections: Optional[Dict[str, Any]]
    consistency_report: Optional[Dict[str, Any]]
    danbooru_tag_records: Optional[List[Any]]
    target_model: Optional[str]
    formatted_prompt: Optional[str]
    final_output: Optional[Dict[str, Any]]
