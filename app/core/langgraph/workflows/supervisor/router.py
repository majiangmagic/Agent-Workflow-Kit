"""Routing helpers for the supervisor workflow."""

from app.core.langgraph.workflows.supervisor.state import SupervisorAction, SupervisorState


def route_by_action(state: SupervisorState) -> SupervisorAction:
    """Return the next action requested by the current state."""

    action = state.get("action")
    if action is None:
        return SupervisorAction.CREATE_PLAN
    return action
