"""Routing helpers for the supervisor agent."""

from app.agents.supervisor.state import SupervisorAction
from app.core.langgraph.workflows.supervisor_simple.state import (
    SupervisorSimpleState,
)


def route_by_action(state: SupervisorSimpleState) -> SupervisorAction:
    """Return the next action requested by the current state."""

    action = state["supervisor"].get("action")
    if action is None:
        return SupervisorAction.CREATE_PLAN
    return action
