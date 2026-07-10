"""State schema for the baseball_analysis_agent agent."""

from typing import Any, Dict, List, Optional, TypedDict

from langchain_core.messages import BaseMessage


class BaseballAnalysisAgentState(TypedDict):
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
    plan: Optional[str]
    task: Optional[str]
    function_detail: Optional[str]
    code: Optional[str]
    execution_result: Optional[Dict[str, Any]]
    answer: Optional[str]
