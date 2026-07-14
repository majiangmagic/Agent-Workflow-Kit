"""State schema for the prompt_writer agent."""

from typing import Any, Dict, List, Optional, TypedDict

from langchain_core.messages import BaseMessage


class PromptWriterState(TypedDict):
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
    danbooru_tags: Optional[List[Any]]
    danbooru_tag_records: Optional[List[Dict[str, Any]]]
    character_prompt: Optional[str]
    character_tags: Optional[List[str]]
    scene_prompt: Optional[str]
    scene_tags: Optional[List[str]]
    special_prompt: Optional[str]
    special_tags: Optional[List[str]]
    draft_prompt: Optional[str]
    negative_prompt: Optional[str]
