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
            "description": "Queries Danbooru tags.",
            "system_prompt": "Query Danbooru tags.",
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


def patch_danbooru(monkeypatch, tags):
    """Keep workflow tests offline while still testing the Danbooru path."""

    async def fake_generate_terms(raw_request, state):
        return ["elaina", "majo no tabitabi", "broom", "forest", "cyberpunk"]

    async def fake_query_tags(terms, limit=20):
        return tags

    monkeypatch.setattr(
        "app.agents.prompt_generation.danbooru_query.nodes."
        "generate_danbooru_search_terms",
        fake_generate_terms,
    )
    monkeypatch.setattr(
        "app.agents.prompt_generation.danbooru_query.nodes.query_danbooru_tags",
        fake_query_tags,
    )


@pytest.mark.asyncio
async def test_prompt_generation_workflow_runs_grouped_agents(monkeypatch):
    """The prompt workflow should pass upstream outputs through grouped agents."""

    patch_danbooru(monkeypatch, ["cyberpunk", "neon_lights", "cityscape"])
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
async def test_prompt_generation_workflow_uses_danbooru_returned_elaina_tags(
    monkeypatch,
):
    """Elaina tags should come from the Danbooru query node, not local mappings."""

    patch_danbooru(
        monkeypatch,
        ["elaina_(majo_no_tabitabi)", "majo_no_tabitabi", "broom", "forest"],
    )
    user_input = "\u4f0a\u857e\u5a1c\u5728\u6797\u95f4\u9a91\u7740\u626b\u5e1a\u98de\u884c"
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
    requirements = nodes["requirement_analyzer"]["requirements_json"]
    tags = nodes["danbooru_query"]["danbooru_tags"]
    final_prompt = nodes["format_converter"]["formatted_prompt"]
    assert requirements["characters"] == []
    assert "elaina_(majo_no_tabitabi)" in tags
    assert "majo_no_tabitabi" in final_prompt
    assert "broom" in final_prompt
    assert "forest" in final_prompt
