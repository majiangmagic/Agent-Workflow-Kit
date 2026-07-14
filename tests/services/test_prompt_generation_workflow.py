"""Tests for the prompt generation workflow example."""

import pytest

from app.core.langgraph.workflows.prompt_generation_workflow.graph import (
    create_prompt_generation_workflow_graph,
)
from app.core.langgraph.workflows.prompt_generation_workflow.state import (
    build_initial_state,
)


def prompt_generation_agents():
    """Return DB-shaped agent configs required by the prompt workflow."""

    return [
        {
            "id": "agent-supervisor",
            "name": "official_supervisor",
            "description": "Coordinates prompt generation.",
            "system_prompt": "Coordinate prompt generation agents.",
            "model": "test-model",
            "temperature": 0.2,
            "tools": [],
        },
        {
            "id": "agent-requirements",
            "name": "prompt_requirement_analyzer",
            "description": "Extracts structured requirements.",
            "system_prompt": "Analyze requirements.",
            "model": "test-model",
            "temperature": 0.2,
            "tools": [],
        },
        {
            "id": "agent-danbooru",
            "name": "prompt_danbooru_query",
            "description": "Maps requirements to Danbooru tags.",
            "system_prompt": "Map tags.",
            "model": "test-model",
            "temperature": 0.2,
            "tools": [],
        },
        {
            "id": "agent-character",
            "name": "character_prompt_generator",
            "description": "Builds character prompts.",
            "system_prompt": "Build character prompt parts.",
            "model": "test-model",
            "temperature": 0.2,
            "tools": [],
        },
        {
            "id": "agent-scene",
            "name": "scene_prompt_generator",
            "description": "Builds scene prompts.",
            "system_prompt": "Build scene prompt parts.",
            "model": "test-model",
            "temperature": 0.2,
            "tools": [],
        },
        {
            "id": "agent-special",
            "name": "special_prompt_generator",
            "description": "Builds special prompt parts.",
            "system_prompt": "Build special prompt parts.",
            "model": "test-model",
            "temperature": 0.2,
            "tools": [],
        },
        {
            "id": "agent-writer",
            "name": "prompt_writer",
            "description": "Writes prompt drafts.",
            "system_prompt": "Write prompts.",
            "model": "test-model",
            "temperature": 0.4,
            "tools": [],
        },
        {
            "id": "agent-reviewer",
            "name": "prompt_reviewer",
            "description": "Reviews prompt drafts.",
            "system_prompt": "Review prompts.",
            "model": "test-model",
            "temperature": 0.2,
            "tools": [],
        },
        {
            "id": "agent-converter",
            "name": "prompt_format_converter",
            "description": "Converts prompt formats.",
            "system_prompt": "Convert prompt formats.",
            "model": "test-model",
            "temperature": 0.2,
            "tools": [],
        },
    ]


@pytest.mark.asyncio
async def test_prompt_generation_workflow_runs_grouped_agents():
    """The prompt workflow should pass upstream outputs through grouped agents."""

    user_input = "Create a flux cyberpunk portrait of a girl in a rainy night city"
    initial_state = build_initial_state(
        crew_id="crew-1",
        agents=prompt_generation_agents(),
        user_id="user-1",
        conversation_id="conversation-1",
        user_input=user_input,
    )
    workflow = create_prompt_generation_workflow_graph(
        crew_id="crew-1",
        agents=prompt_generation_agents(),
    )

    result = await workflow.ainvoke(
        initial_state,
        config={"configurable": {"thread_id": "prompt-generation-test"}},
    )

    nodes = result["nodes"]
    assert nodes["requirement_analyzer"]["requirements_json"]["target_model"] == "flux"
    assert nodes["character_prompt_generator"]["character_prompt"]
    assert nodes["scene_prompt_generator"]["scene_prompt"]
    assert nodes["special_prompt_generator"]["special_prompt"]
    assert "cyberpunk" in nodes["danbooru_query"]["danbooru_tags"]
    assert "neon_lights" in nodes["prompt_writer"]["draft_prompt"]
    assert nodes["prompt_reviewer"]["review_result"]["approved"] is True
    assert nodes["format_converter"]["final_output"]["target_model"] == "flux"
    assert "Create an image of" in nodes["format_converter"]["formatted_prompt"]


@pytest.mark.asyncio
async def test_prompt_generation_workflow_keeps_elaina_tags():
    user_input = "伊蕾娜在林间骑着扫帚飞行"
    initial_state = build_initial_state(
        crew_id="crew-1",
        agents=prompt_generation_agents(),
        user_id="user-1",
        conversation_id="conversation-elaina",
        user_input=user_input,
    )
    workflow = create_prompt_generation_workflow_graph(
        crew_id="crew-1",
        agents=prompt_generation_agents(),
    )

    result = await workflow.ainvoke(
        initial_state,
        config={"configurable": {"thread_id": "prompt-generation-elaina-test"}},
    )

    nodes = result["nodes"]
    tags = nodes["danbooru_query"]["danbooru_tags"]
    final_prompt = nodes["format_converter"]["formatted_prompt"]
    assert "elaina_(majo_no_tabitabi)" in tags
    assert "majo_no_tabitabi" in final_prompt
    assert "broom" in final_prompt
    assert "forest" in final_prompt
