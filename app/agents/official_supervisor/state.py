"""State and action types owned by the official supervisor agent."""

from enum import Enum
from typing import Annotated, Any, Dict, List, Literal, Optional, TypedDict

from langgraph.managed import RemainingSteps
from typing_extensions import NotRequired

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class SupervisorAction(str, Enum):
    """Actions that the supervisor agent can request."""

    ANSWER_DIRECTLY = "answer_directly"
    CREATE_PLAN = "create_plan"
    ASSIGN_TASKS = "assign_tasks"
    CHECK_STATUS = "check_status"
    COMBINE_RESULTS = "combine_results"


class DelegatedAgentState(TypedDict):
    """Task-level state tracked by the supervisor for a delegated agent."""

    agent_id: str
    agent_name: str
    description: Optional[str]
    system_prompt: Optional[str]
    model: Optional[str]
    temperature: float
    messages: List[BaseMessage]
    status: Literal["idle", "working", "complete", "error"]
    results: Optional[Dict[str, Any]]
    error: Optional[str]
    tools: List[Dict[str, Any]]


class SupervisorState(TypedDict):
    """Runtime state for an agent running the supervisor implementation."""

    agent_id: str
    agent_name: str
    description: Optional[str]
    system_prompt: Optional[str]
    model: Optional[str]
    temperature: float
    tools: List[Dict[str, Any]]
    messages: Annotated[List[BaseMessage], add_messages]
    user_input: Optional[str]
    workflow_inputs: Dict[str, Any]
    plan: Optional[Dict[str, Any]]
    action: Optional[SupervisorAction]
    agents: Dict[str, DelegatedAgentState]
    next_node: NotRequired[str]
    long_term_memories: NotRequired[List[Dict[str, Any]]]
    remaining_steps: NotRequired[RemainingSteps]
