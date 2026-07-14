"""State schema for the scene_prompt_generator agent."""

from typing import Any, Dict, List, Optional, TypedDict

from langchain_core.messages import BaseMessage


class ScenePromptGeneratorState(TypedDict):
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
    workflow_inputs: Dict[str, Any]

    # 下面是 DSL 声明的业务状态字段。
    requirements_json: Optional[Dict[str, Any]]
    scene_prompt: Optional[str]
    scene_tags: Optional[List[Any]]
    danbooru_tag_records: Optional[List[Any]]
    danbooru_search_terms: Optional[List[Any]]
