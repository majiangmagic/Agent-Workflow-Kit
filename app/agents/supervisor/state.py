"""State types for the supervisor agent workflow nodes."""

import uuid
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, TypedDict

from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """State maintained for each agent in the system."""

    agent_id: str
    agent_name: str
    messages: List[BaseMessage]
    status: Literal["idle", "working", "complete", "error"]
    results: Optional[Dict[str, Any]]
    tools: List[Dict[str, Any]]


class SupervisorAction(str, Enum):
    """Actions that the supervisor agent can request."""

    ANSWER_DIRECTLY = "answer_directly"
    CREATE_PLAN = "create_plan"
    ASSIGN_TASKS = "assign_tasks"
    CHECK_STATUS = "check_status"
    COMBINE_RESULTS = "combine_results"


class SupervisorState(TypedDict):
    """Shared state maintained by the supervisor agent nodes."""

    messages: List[BaseMessage]
    user_input: Optional[str]
    plan: Optional[Dict[str, Any]]
    agents: Dict[str, AgentState]
    crew_id: str
    conversation_id: str
    action: Optional[SupervisorAction]


def build_initial_state(crew_id: str, agents: List[Dict]) -> SupervisorState:
    """Build the initial state for a supervisor run."""

    agent_states = {}
    for agent_config in agents:
        agent_id = agent_config.get("id") or str(uuid.uuid4())
        agent_states[agent_id] = {
            "agent_id": agent_id,
            "agent_name": agent_config["name"],
            "messages": [],
            "status": "idle",
            "results": None,
            "tools": agent_config.get("tools", []),
        }

    return {
        "messages": [],
        "user_input": None,
        "plan": None,
        "agents": agent_states,
        "crew_id": crew_id,
        "conversation_id": "",
        "action": None,
    }
