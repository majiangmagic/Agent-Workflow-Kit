"""Shared state for the simple supervisor workflow."""

import uuid
from typing import Dict, List, TypedDict

from app.agents.base import AgentState
from app.agents.supervisor.state import SupervisorState


class SupervisorSimpleState(TypedDict):
    """Global state passed through the simple supervisor workflow."""

    supervisor: SupervisorState
    agents: Dict[str, AgentState]
    crew_id: str
    conversation_id: str


def build_initial_state(crew_id: str, agents: List[Dict]) -> SupervisorSimpleState:
    """Build the initial global state for a supervisor workflow run."""

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
        "supervisor": {
            "messages": [],
            "user_input": None,
            "plan": None,
            "action": None,
            "agents": agent_states,
        },
        "agents": agent_states,
        "crew_id": crew_id,
        "conversation_id": "",
    }
