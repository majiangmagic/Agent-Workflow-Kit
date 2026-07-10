"""Declarative workflow building blocks.

Workflow modules should describe nodes and edges here, then let the shared
compiler build LangGraph objects and initial state mechanically.
"""

from dataclasses import dataclass, field
from typing import Annotated, Any, Dict, List, Optional, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph import END, StateGraph

from app.agents.registry import agent_registry
from app.core.langgraph.checkpoint import get_checkpointer
from app.core.langgraph.workflows.adapters.agent import (
    AgentNodeExtensionFactory,
    create_agent_node,
)


def normalize_node_name(name: str) -> str:
    """Normalize names used to bind workflow nodes to agent configs."""

    return name.strip().lower().replace(" ", "_")


def merge_node_states(
    current: Optional[Dict[str, Dict[str, Any]]],
    update: Optional[Dict[str, Dict[str, Any]]],
) -> Dict[str, Dict[str, Any]]:
    """Merge node updates into checkpointed workflow state."""

    if not current:
        return update or {}
    if not update:
        return current

    merged = {**current}
    for node_name, node_update in update.items():
        node_current = current.get(node_name, {})
        node_merged = {**node_current, **node_update}
        if node_update.get("messages") == [] and node_current.get("messages"):
            node_merged["messages"] = node_current["messages"]
        merged[node_name] = node_merged
    return merged


class WorkflowState(TypedDict):
    """Generic global workflow state shared by generated workflows."""

    nodes: Annotated[Dict[str, Dict[str, Any]], merge_node_states]
    agents: Dict[str, Dict[str, Any]]
    crew_id: str
    conversation_id: str
    user_input: Optional[str]


@dataclass(frozen=True)
class WorkflowNodeSpec:
    """Declarative description of one workflow node."""

    name: str
    agent: Optional[str] = None
    state_agent: Optional[str] = None
    extension_factory: Optional[AgentNodeExtensionFactory] = None


@dataclass(frozen=True)
class WorkflowEdgeSpec:
    """Declarative description of one directed workflow edge."""

    source: str
    target: str


@dataclass(frozen=True)
class WorkflowDefinition:
    """A workflow graph that can be generated from data."""

    name: str
    entrypoint: str
    nodes: List[WorkflowNodeSpec]
    edges: List[WorkflowEdgeSpec] = field(default_factory=list)


def build_agent_runtime_state(
    node: WorkflowNodeSpec,
    agent_config: Dict[str, Any],
    user_input: Optional[str],
    messages: Optional[List[BaseMessage]] = None,
) -> Dict[str, Any]:
    """Project a DB agent config into a node-local runtime state."""

    agent_key = agent_config.get("id") or node.name
    return {
        "agent_id": str(agent_key),
        "agent_name": agent_config.get("name", node.name),
        "description": agent_config.get("description"),
        "system_prompt": agent_config.get("system_prompt"),
        "model": agent_config.get("model"),
        "temperature": agent_config.get("temperature", 0.2),
        "tools": agent_config.get("tools", []),
        "messages": messages or [],
        "user_input": user_input,
        "plan": None,
        "action": None,
        "agents": {},
        "status": "idle",
        "results": None,
        "error": None,
    }


def build_workflow_initial_state(
    definition: WorkflowDefinition,
    crew_id: str,
    agents: List[Dict[str, Any]],
    conversation_id: str = "",
    messages: Optional[List[BaseMessage]] = None,
    user_input: Optional[str] = None,
) -> WorkflowState:
    """Build initial state from a workflow definition and agent configs."""

    agents_by_name = {
        normalize_node_name(agent_config["name"]): agent_config
        for agent_config in agents
    }
    agent_catalog = {
        node_name: build_agent_runtime_state(
            node=WorkflowNodeSpec(name=node_name),
            agent_config=agent_config,
            user_input=user_input,
            messages=[],
        )
        for node_name, agent_config in agents_by_name.items()
    }
    node_states = {}
    for node in definition.nodes:
        state_agent_name = normalize_node_name(node.state_agent or node.name)
        agent_config = agents_by_name.get(state_agent_name)
        if agent_config is None:
            raise ValueError(
                f"Workflow '{definition.name}' requires an agent named "
                f"'{node.state_agent or node.name}'"
            )
        node_states[node.name] = build_agent_runtime_state(
            node=node,
            agent_config=agent_config,
            user_input=user_input,
            messages=messages,
        )

    return {
        "nodes": node_states,
        "agents": agent_catalog,
        "crew_id": crew_id,
        "conversation_id": conversation_id,
        "user_input": user_input,
    }


def compile_workflow_definition(definition: WorkflowDefinition):
    """Compile a declarative workflow definition into a LangGraph."""

    workflow = StateGraph(WorkflowState)
    for node in definition.nodes:
        agent_name = node.agent or node.name
        agent_graph_factory = agent_registry.get(agent_name)
        if agent_graph_factory is None:
            raise ValueError(f"Agent graph factory '{agent_name}' is not registered")

        extension = (
            node.extension_factory(node.name)
            if node.extension_factory is not None
            else None
        )
        workflow.add_node(
            node.name,
            create_agent_node(
                node.name,
                agent_graph_factory(),
                extension=extension,
            ),
        )

    for edge in definition.edges:
        target = END if edge.target == END else edge.target
        workflow.add_edge(edge.source, target)

    workflow.set_entry_point(definition.entrypoint)
    return workflow.compile(checkpointer=get_checkpointer())
