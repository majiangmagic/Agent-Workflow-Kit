"""State schema for the natural_language_editor agent."""

from typing import Any, Dict, List, Optional, TypedDict

from langchain_core.messages import BaseMessage


class NaturalLanguageEditorState(TypedDict):
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
    turn_intent: Optional[str]
    edit_operations: Optional[List[Any]]
    request_contract: Optional[Dict[str, Any]]
    resolved_user_request: Optional[str]
    editor_succeeded: Optional[bool]
