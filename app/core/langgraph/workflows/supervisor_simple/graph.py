"""Workflow graph for the simple supervisor collaboration pattern."""

from typing import Dict, List

from langgraph.graph import END, StateGraph

import app.agents.supervisor.graph  # noqa: F401
from app.agents.registry import agent_registry
from app.core.langgraph.checkpoint import get_checkpointer
from app.core.langgraph.workflows.adapters.agent import create_agent_node
from app.core.langgraph.workflows.adapters.supervisor import create_supervisor_extension
from app.core.langgraph.workflows.supervisor_simple.state import (
    SUPERVISOR_NODE_NAME,
    SupervisorSimpleState,
    build_initial_state,
    normalize_node_name,
)
from app.core.langgraph.workflows.registry import workflow_registry


def create_supervisor_simple_graph(
    crew_id: str,
    agents: List[Dict],
):
    """Create a compiled LangGraph for a simple supervisor agent crew."""

    supervisor_agent = next(
        (
            agent
            for agent in agents
            if normalize_node_name(agent["name"]) == SUPERVISOR_NODE_NAME
        ),
        None,
    )

    workflow = StateGraph(SupervisorSimpleState)
    supervisor_graph_factory = agent_registry.get(SUPERVISOR_NODE_NAME)
    if supervisor_graph_factory is None:
        raise ValueError("Agent graph factory 'supervisor' is not registered")
    if supervisor_agent is None:
        raise ValueError("Workflow requires an agent named 'supervisor'")
    supervisor_graph = supervisor_graph_factory()

    workflow.add_node(
        SUPERVISOR_NODE_NAME,
        create_agent_node(
            SUPERVISOR_NODE_NAME,
            supervisor_graph,
            extension=create_supervisor_extension(workflow),
        ),
    )
    workflow.add_edge(SUPERVISOR_NODE_NAME, END)
    workflow.set_entry_point(SUPERVISOR_NODE_NAME)

    return workflow.compile(checkpointer=get_checkpointer())


workflow_registry.register(
    "supervisor_simple",
    create_supervisor_simple_graph,
    state_builder=build_initial_state,
)
