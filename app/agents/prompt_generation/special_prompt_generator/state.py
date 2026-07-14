"""State schema for the special_prompt_generator agent."""

from typing import Any, Dict, List, Optional, TypedDict

from langchain_core.messages import BaseMessage


class SpecialPromptGeneratorState(TypedDict):
    agent_id: str
    agent_name: str
    description: Optional[str]
    system_prompt: Optional[str]
    model: Optional[str]
    temperature: float
    tools: List[Dict[str, Any]]
    messages: List[BaseMessage]
    user_input: Optional[str]
    requirements_json: Optional[Dict[str, Any]]
    danbooru_tag_records: Optional[List[Dict[str, Any]]]
    special_prompt: Optional[str]
    special_tags: Optional[List[str]]
