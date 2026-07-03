"""Backward-compatible imports for the supervisor workflow.

New code should import from app.core.langgraph.workflows.supervisor_simple or
app.agents.supervisor.
"""

from app.core.langgraph.workflows.supervisor_simple import (
    AgentState,
    SupervisorSimpleAction,
    SupervisorSimpleState,
    build_initial_state,
    create_supervisor_simple_graph,
)

SupervisorAction = SupervisorSimpleAction
SupervisorState = SupervisorSimpleState
create_supervisor_graph = create_supervisor_simple_graph

__all__ = [
    "AgentState",
    "SupervisorAction",
    "SupervisorState",
    "build_initial_state",
    "create_supervisor_graph",
]
