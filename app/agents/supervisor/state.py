"""State and action types owned by the supervisor agent."""

from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict

from langchain_core.messages import BaseMessage

from app.agents.base import AgentState


class SupervisorAction(str, Enum):
    """Actions that the supervisor agent can request."""

    ANSWER_DIRECTLY = "answer_directly"
    CREATE_PLAN = "create_plan"
    ASSIGN_TASKS = "assign_tasks"
    CHECK_STATUS = "check_status"
    COMBINE_RESULTS = "combine_results"


class SupervisorState(TypedDict):
    """State owned by the supervisor agent within a workflow run."""

    messages: List[BaseMessage]
    user_input: Optional[str]
    plan: Optional[Dict[str, Any]]
    action: Optional[SupervisorAction]


class SupervisorRuntimeState(SupervisorState):
    """Runtime state used inside the supervisor agent graph."""

    agents: Dict[str, AgentState]
