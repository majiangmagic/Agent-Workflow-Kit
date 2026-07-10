"""Public API for the baseball_analysis_workflow workflow."""

from app.core.langgraph.workflows.baseball_analysis_workflow.state import (
    BaseballAnalysisWorkflowState,
    build_initial_state,
)


def __getattr__(name: str):
    if name == "create_baseball_analysis_workflow_graph":
        from app.core.langgraph.workflows.baseball_analysis_workflow.graph import create_baseball_analysis_workflow_graph

        return create_baseball_analysis_workflow_graph
    raise AttributeError(name)


__all__ = [
    "BaseballAnalysisWorkflowState",
    "build_initial_state",
    "create_baseball_analysis_workflow_graph",
]
