"""Graph factory for the baseball_analysis_workflow workflow."""

from typing import Any, Dict, List

import app.agents.baseball_analysis_agent.graph  # noqa: F401
import app.agents.official_supervisor.graph  # noqa: F401
from app.core.langgraph.workflows.declarative import compile_workflow_definition
from app.core.langgraph.workflows.registry import workflow_registry
from app.core.langgraph.workflows.baseball_analysis_workflow.spec import WORKFLOW_DEFINITION
from app.core.langgraph.workflows.baseball_analysis_workflow.state import build_initial_state


def create_baseball_analysis_workflow_graph(
    crew_id: str,
    agents: List[Dict[str, Any]],
):
    """Create a compiled LangGraph from the declarative workflow spec."""

    return compile_workflow_definition(WORKFLOW_DEFINITION)


workflow_registry.register(
    WORKFLOW_DEFINITION.name,
    create_baseball_analysis_workflow_graph,
    state_builder=build_initial_state,
)
