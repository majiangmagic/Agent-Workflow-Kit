"""Shared state for the simple supervisor workflow."""

from typing import Annotated, Dict, List, Optional, TypedDict

from langchain_core.messages import BaseMessage
from app.agents.supervisor.state import SupervisorState


def merge_supervisor_state(
    current: Optional[SupervisorState],
    update: Optional[SupervisorState],
) -> SupervisorState:
    """Merge per-turn supervisor input into checkpointed workflow state."""

    if not current:
        return update or {
            "messages": [],
            "user_input": None,
            "plan": None,
            "action": None,
            "agents": {},
        }
    if not update:
        return current

    merged = {**current, **update}
    if update.get("messages") == [] and current.get("messages"):
        merged["messages"] = current["messages"]
    return merged


class SupervisorSimpleState(TypedDict):
    """Global state passed through the simple supervisor workflow."""

    supervisor: Annotated[SupervisorState, merge_supervisor_state]
    crew_id: str
    conversation_id: str


def build_initial_state(
    crew_id: str,
    agents: List[Dict],
    conversation_id: str = "",
    messages: Optional[List[BaseMessage]] = None,
    user_input: Optional[str] = None,
) -> SupervisorSimpleState:
    """Build the initial global state for a supervisor workflow run."""

    agent_states = {}
    for agent_config in agents:
        agent_key = agent_config.get("id") or agent_config["name"]
        agent_states[agent_key] = {
            "agent_id": str(agent_key),
            "agent_name": agent_config["name"],
            "description": agent_config.get("description"),
            "system_prompt": agent_config.get("system_prompt"),
            "model": agent_config.get("model"),
            "temperature": agent_config.get("temperature", 0.2),
            "messages": [],
            "status": "idle",
            "results": None,
            "error": None,
            "tools": agent_config.get("tools", []),
        }

    return {
        "supervisor": {
            "messages": [],
            "user_input": user_input,
            "plan": None,
            "action": None,
            "agents": agent_states,
        },
        "crew_id": crew_id,
        "conversation_id": conversation_id,
    }
