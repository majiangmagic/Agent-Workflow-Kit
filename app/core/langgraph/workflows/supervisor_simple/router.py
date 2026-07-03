"""Routing helpers for the simple supervisor workflow."""

from app.core.langgraph.workflows.supervisor_simple.state import (
    SupervisorSimpleAction,
    SupervisorSimpleState,
)


def route_by_action(state: SupervisorSimpleState) -> SupervisorSimpleAction:
    """Return the next action requested by the current state."""

    action = state.get("action")
    if action is None:
        return SupervisorSimpleAction.CREATE_PLAN
    return action
