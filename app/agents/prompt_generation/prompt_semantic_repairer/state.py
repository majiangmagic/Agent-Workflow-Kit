"""State schema for the prompt_semantic_repairer agent."""

from typing import Any, Dict, List, Optional, TypedDict

from langchain_core.messages import BaseMessage


class PromptSemanticRepairerState(TypedDict):
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
    scene_document: Optional[Dict[str, Any]]
    resolved_prompt_ir: Optional[Dict[str, Any]]
    validation_report: Optional[Dict[str, Any]]
    repair_overlay: Optional[Dict[str, Any]]
    repair_attempts: Optional[int]
