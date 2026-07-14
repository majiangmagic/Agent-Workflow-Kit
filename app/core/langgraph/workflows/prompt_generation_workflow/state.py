"""State helpers for the prompt_generation_workflow workflow."""

from typing import Any, Dict, List, Optional

from langchain_core.messages import BaseMessage

from app.core.langgraph.workflows.declarative import (
    WorkflowState,
    build_workflow_initial_state,
    merge_node_states,
)

PromptGenerationWorkflowState = WorkflowState

WORKFLOW_NAME = "prompt_generation_workflow"
NODE_AGENTS = {
    "supervisor": "official_supervisor",
    "requirement_analyzer": "prompt_requirement_analyzer",
    "character_prompt_generator": "character_prompt_generator",
    "scene_prompt_generator": "scene_prompt_generator",
    "special_prompt_generator": "special_prompt_generator",
    "danbooru_query": "prompt_danbooru_query",
    "prompt_writer": "prompt_writer",
    "prompt_reviewer": "prompt_reviewer",
    "format_converter": "prompt_format_converter",
}


def _with_default_prompt_agents(agents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Allow old demo crews to run after the workflow adds deterministic nodes."""

    agents_by_name = {
        str(agent.get("name", "")).strip().lower().replace(" ", "_")
        for agent in agents
    }
    completed = list(agents)
    for agent_name in NODE_AGENTS.values():
        if agent_name in agents_by_name:
            continue
        completed.append(
            {
                "id": f"default-{agent_name}",
                "name": agent_name,
                "description": f"Default runtime config for {agent_name}.",
                "system_prompt": f"Run {agent_name}.",
                "model": "local-deterministic",
                "temperature": 0.2,
                "tools": [],
            }
        )
    return completed


def build_initial_state(
    crew_id: str,
    agents: List[Dict[str, Any]],
    user_id: str = "",
    conversation_id: str = "",
    messages: Optional[List[BaseMessage]] = None,
    user_input: Optional[str] = None,
) -> WorkflowState:
    """Build initial state for this workflow definition."""

    return build_workflow_initial_state(
        workflow_name=WORKFLOW_NAME,
        node_agents=NODE_AGENTS,
        user_id=user_id,
        crew_id=crew_id,
        agents=_with_default_prompt_agents(agents),
        conversation_id=conversation_id,
        messages=messages,
        user_input=user_input,
    )
