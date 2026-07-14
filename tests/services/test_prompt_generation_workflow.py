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


def patch_danbooru(monkeypatch, records):
    """Keep workflow tests offline while still testing the Danbooru path."""

    async def fake_generate_terms(raw_request, state):
        return ["candidate-from-llm"]

    async def fake_query_records(terms, limit=20):
        return records

    monkeypatch.setattr(
        "app.agents.prompt_generation.danbooru_query.nodes."
        "generate_danbooru_search_terms",
        fake_generate_terms,
    )
    monkeypatch.setattr(
        "app.agents.prompt_generation.danbooru_query.nodes."
        "query_danbooru_tag_records",
        fake_query_records,
    )


@pytest.mark.asyncio
async def test_prompt_generation_workflow_uses_only_danbooru_records(monkeypatch):
    """The prompt workflow should pass Danbooru records through grouped agents."""

    patch_danbooru(
        monkeypatch,
        [
            {"name": "returned_character_tag", "category": 4, "post_count": 100},
            {"name": "returned_general_tag", "category": 0, "post_count": 90},
        ],
    )
    initial_state = build_initial_state(
        crew_id="crew-1",
        agents=prompt_generation_agents(),
        user_id="user-1",
        conversation_id="conversation-1",
        user_input="user supplied image request",
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
    assert nodes["danbooru_query"]["danbooru_tags"] == [
        "returned_character_tag",
        "returned_general_tag",
    ]
    assert nodes["character_prompt_generator"]["character_tags"] == [
        "returned_character_tag"
    ]
    assert nodes["scene_prompt_generator"]["scene_tags"] == ["returned_general_tag"]
    assert nodes["special_prompt_generator"]["special_tags"] == []
    assert nodes["prompt_writer"]["draft_prompt"] == (
        "returned_character_tag, returned_general_tag"
    )
    assert nodes["prompt_reviewer"]["review_result"]["approved"] is True


@pytest.mark.asyncio
async def test_prompt_generation_workflow_does_not_fallback_to_preset_tags(
    monkeypatch,
):
    """No Danbooru hit means no prompt tags, not local default quality tags."""

    patch_danbooru(monkeypatch, [])
    initial_state = build_initial_state(
        crew_id="crew-1",
        agents=prompt_generation_agents(),
        user_id="user-1",
        conversation_id="conversation-empty",
        user_input="request with no external tag hits",
    )
    workflow = create_prompt_generation_workflow_graph(
        crew_id="crew-1",
        agents=prompt_generation_agents(),
    )

    result = await workflow.ainvoke(
        initial_state,
        config={"configurable": {"thread_id": "prompt-generation-empty-test"}},
    )

    nodes = result["nodes"]
    assert nodes["danbooru_query"]["danbooru_tags"] == []
    assert nodes["prompt_writer"]["draft_prompt"] == ""
    assert nodes["prompt_reviewer"]["review_result"]["approved"] is False
    assert "no_danbooru_tags_found" in nodes["prompt_reviewer"]["review_result"]["issues"]
