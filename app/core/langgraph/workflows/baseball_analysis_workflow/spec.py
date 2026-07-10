"""Declarative spec for the baseball_analysis_workflow workflow."""

from langgraph.graph import END
from app.core.langgraph.workflows.adapters.supervisor import create_supervisor_extension
from app.core.langgraph.workflows.declarative import (
    WorkflowDefinition,
    WorkflowEdgeSpec,
    WorkflowNodeSpec,
)

BASEBALL_ANALYSIS_WORKFLOW_WORKFLOW_NAME = "baseball_analysis_workflow"
BASEBALL_ANALYSIS_WORKFLOW_ENTRYPOINT = "supervisor"
BASEBALL_ANALYSIS_AGENT_AGENT_NAME = "baseball_analysis_agent"
OFFICIAL_SUPERVISOR_AGENT_NAME = "official_supervisor"

WORKFLOW_DEFINITION = WorkflowDefinition(
    name=BASEBALL_ANALYSIS_WORKFLOW_WORKFLOW_NAME,
    entrypoint=BASEBALL_ANALYSIS_WORKFLOW_ENTRYPOINT,
    nodes=[
        WorkflowNodeSpec(
            name="supervisor",
            agent="official_supervisor",
            extension_factory=create_supervisor_extension,
        ),
        WorkflowNodeSpec(
            name="baseball_analyst",
            agent="baseball_analysis_agent",
        ),
    ],
    edges=[
        WorkflowEdgeSpec(source="supervisor", target='baseball_analyst'),
        WorkflowEdgeSpec(source="baseball_analyst", target=END),
    ],
)
