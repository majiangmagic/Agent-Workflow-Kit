"""Workflow graph for the simple supervisor collaboration pattern."""

from typing import Any, Dict, List

from langgraph.graph import END, StateGraph

from app.agents.supervisor.graph import create_supervisor_graph
from app.agents.supervisor.state import SupervisorState
from app.core.langgraph.workflows.supervisor_simple.state import (
    SupervisorSimpleState,
)
from app.core.langgraph.workflows.registry import workflow_registry


def create_supervisor_simple_graph(
    crew_id: str, agents: List[Dict], system_prompt: str = None
):
    """Create a compiled LangGraph for a simple supervisor agent crew."""

    supervisor_graph = create_supervisor_graph()

    def run_supervisor(state: SupervisorSimpleState) -> Dict[str, Any]:
        """Adapt workflow state into supervisor state and write the result back."""

        supervisor_state: SupervisorState = {
            **state["supervisor"],
            "agents": state["agents"],
        }
        updated_supervisor_state = supervisor_graph.invoke(supervisor_state)

        return {
            **state,
            "supervisor": updated_supervisor_state,
            "agents": updated_supervisor_state["agents"],
        }

    workflow = StateGraph(SupervisorSimpleState)

    workflow.add_node("supervisor", run_supervisor)
    workflow.add_edge("supervisor", END)
    workflow.set_entry_point("supervisor")

    return workflow.compile()


workflow_registry.register("supervisor_simple", create_supervisor_simple_graph)
