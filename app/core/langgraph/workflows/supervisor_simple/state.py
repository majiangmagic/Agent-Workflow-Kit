"""State helpers for the simple supervisor workflow."""

from typing import Any, Dict, List, Optional

from langchain_core.messages import BaseMessage

from app.core.langgraph.workflows.declarative import (
    WorkflowState,
    build_workflow_initial_state,
    merge_node_states,
)
from app.core.langgraph.workflows.supervisor_simple.spec import WORKFLOW_DEFINITION

SupervisorSimpleState = WorkflowState


def build_initial_state(
    crew_id: str,
    agents: List[Dict[str, Any]],
    conversation_id: str = "",
    messages: Optional[List[BaseMessage]] = None,
    user_input: Optional[str] = None,
) -> WorkflowState:
    """Build initial state for the supervisor workflow definition."""

    return build_workflow_initial_state(
        definition=WORKFLOW_DEFINITION,
        crew_id=crew_id,
        agents=agents,
        conversation_id=conversation_id,
        messages=messages,
        user_input=user_input,
    )
