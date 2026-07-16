"""Tests for the SceneDocument-based prompt generation workflow."""

from __future__ import annotations

import json
import uuid

import pytest
from langchain_core.messages import AIMessage

from app.agents.catalog import resolve_workflow_agent_configs
from app.agents.prompt_generation.domain import (
    apply_patch_proposal,
    collect_required_paths,
    compute_impact_set,
    empty_scene_document,
    normalize_scene_document,
    validate_patch_proposal,
)
from app.agents.prompt_generation.prompt_compiler.nodes import compile_prompt_node
from app.agents.prompt_generation.prompt_consistency_validator.nodes import (
    validate_prompt_node,
)
from app.agents.prompt_generation.prompt_target_renderer.nodes import render_prompt_node
from app.api.routes.conversation import extract_workflow_memory
from app.core.langgraph.workflows.prompt_generation_workflow.graph import (
    WORKFLOW_METADATA,
    create_prompt_generation_workflow_graph,
)
from app.core.langgraph.workflows.prompt_generation_workflow.state import build_initial_state


def sample_document(name: str = "Hatsune Miku", version: int = 1):
    return normalize_scene_document(
        {
            "summary": f"{name} walking on a street",
            "participants": {
                "character_1": {
                    "adult": True,
                    "identity": {"input_name": name},
                    "actions": ["walking"],
                }
            },
            "environment": {"location": "street"},
            "relations": {
                "relation_1": {
                    "subject": "external_hand",
                    "predicate": "pull",
                    "object": "character_1",
                    "instrument": "rope",
                }
            },
        },
        version=version,
    )


def runtime_agents():
    return resolve_workflow_agent_configs(WORKFLOW_METADATA)


def test_patch_replaces_identity_without_rewriting_bound_actions_or_relations():
    document = sample_document()
    proposal = validate_patch_proposal(
        {
            "base_version": 1,
            "intent": "replace_character",
            "operations": [
                {
                    "op": "replace",
                    "path": "/participants/character_1/identity",
                    "value": {"input_name": "Moria Luluka"},
                }
            ],
        },
        1,
    )

    updated = apply_patch_proposal(document, proposal)

    assert updated["version"] == 2
    assert updated["participants"]["character_1"]["identity"]["input_name"] == "Moria Luluka"
    assert updated["participants"]["character_1"]["actions"] == ["walking"]
    assert updated["relations"]["relation_1"]["object"] == "character_1"


def test_patch_rejects_dangling_participant_relations():
    document = sample_document()
    proposal = validate_patch_proposal(
        {
            "base_version": 1,
            "operations": [
                {"op": "remove", "path": "/participants/character_1"}
            ],
        },
        1,
    )

    with pytest.raises(ValueError, match="missing participant"):
        apply_patch_proposal(document, proposal)


def test_identity_only_change_does_not_invalidate_visual_resolution():
    previous = sample_document()
    current = sample_document("Moria Luluka", version=2)

    impact = compute_impact_set(previous, current)

    assert impact["identity_changed"] is True
    assert impact["visual_changed"] is False
    assert "Hatsune Miku" in impact["removed_identity_terms"]


def test_document_normalization_removes_identity_duplicates_from_requirements():
    document = normalize_scene_document(
        {
            "participants": {
                "character_1": {"identity": {"input_name": "Hatsune Miku"}}
            },
            "requirements": {
                "positive": ["Hatsune Miku", "standing"],
                "required": ["Hatsune Miku", "full body"],
            },
        }
    )

    assert document["requirements"]["positive"] == ["standing"]
    assert document["requirements"]["required"] == ["full body"]


def test_compiler_removes_old_identity_and_applies_repair_overlay():
    result = compile_prompt_node(
        {
            "scene_document": sample_document("Moria Luluka", version=2),
            "impact_set": {"removed_identity_terms": ["hatsune_miku"]},
            "identity_terms": [
                {"value": "moria_luluka", "source_path": "/participants/character_1/identity"},
                {"value": "hatsune_miku", "source_path": "/participants/character_1/identity"},
            ],
            "atomic_terms": [{"value": "street", "source_path": "/environment/location"}],
            "relation_terms": [],
            "negative_terms": [{"value": "text", "source_path": "/requirements/negative/0"}],
            "identity_tag_records": [],
            "visual_tag_records": [],
            "repair_overlay": {
                "remove_positive": ["street"],
                "add_positive": [
                    {"value": "city street", "source_path": "/environment/location"}
                ],
            },
        }
    )
    values = [item["value"] for item in result["resolved_prompt_ir"]["positive_terms"]]

    assert "moria_luluka" in values
    assert "hatsune_miku" not in values
    assert "street" not in values
    assert "city street" in values


def test_validator_reports_missing_paths_and_polarity_conflicts():
    document = sample_document()
    result = validate_prompt_node(
        {
            "scene_document": document,
            "impact_set": {"removed_identity_terms": []},
            "resolved_prompt_ir": {
                "positive_terms": [{"value": "street", "source_path": "/environment/location"}],
                "compiled_negative_terms": [{"value": "street", "source_path": "/requirements/negative/0"}],
                "covered_paths": ["/environment/location"],
            },
        }
    )

    assert result["needs_repair"] is True
    assert "positive_negative_conflict" in result["validation_report"]["issues"]
    assert set(result["validation_report"]["missing_paths"]) == (
        set(collect_required_paths(document)) - {"/environment/location"}
    )


def test_renderer_keeps_phrases_for_nai_v4_but_not_nai_v3():
    state = {
        "scene_document": sample_document(),
        "resolved_prompt_ir": {
            "positive_terms": [
                {"value": "hatsune_miku", "kind": "verified_identity_tag"},
                {"value": "a hand pulling her by a rope", "kind": "relation_phrase"},
            ],
            "compiled_negative_terms": [],
            "danbooru_tag_records": [{"name": "hatsune_miku"}],
        },
        "validation_report": {"valid": True},
    }
    v4 = render_prompt_node({**state, "workflow_inputs": {"target_model": "nai_v4"}})
    v3 = render_prompt_node({**state, "workflow_inputs": {"target_model": "nai_v3"}})

    assert "a hand pulling her by a rope" in v4["final_output"]["positive_prompt"]
    assert "a hand pulling her by a rope" not in v3["final_output"]["positive_prompt"]
    assert "hatsune_miku" in v3["final_output"]["positive_prompt"]


class WorkflowModel:
    """Deterministic structured responses for two workflow turns."""

    async def ainvoke(self, messages):
        system = str(messages[0].content)
        payload = str(messages[-1].content)
        if "base_version" in system and "SceneDocument" in system:
            if "replace character" in payload:
                content = {
                    "base_version": 1,
                    "intent": "replace_character",
                    "operations": [
                        {
                            "op": "replace",
                            "path": "/participants/character_1/identity",
                            "value": {"input_name": "Moria Luluka"},
                            "evidence": "replace character",
                        }
                    ],
                }
            else:
                document = sample_document(version=0)
                document.pop("version", None)
                document["relations"] = {}
                content = {
                    "base_version": 0,
                    "intent": "create",
                    "operations": [{"op": "replace", "path": "/", "value": document}],
                }
            return AIMessage(content=json.dumps(content))
        if "danbooru_tag_candidates" in system:
            name = "Moria Luluka" if "Moria Luluka" in payload else "Hatsune Miku"
            tag = "moria_luluka" if name == "Moria Luluka" else "hatsune_miku"
            return AIMessage(
                content=json.dumps(
                    {
                        "identities": [
                            {
                                "participant_id": "character_1",
                                "input_name": name,
                                "canonical_name": name,
                                "series": "test",
                                "danbooru_tag_candidates": [tag],
                            }
                        ]
                    }
                )
            )
        if "atomic_facts" in system:
            return AIMessage(
                content=json.dumps(
                    {
                        "atomic_facts": [
                            {
                                "source_path": "/participants/character_1/actions/0",
                                "candidates": ["walking"],
                                "fallback_phrase": "walking",
                            },
                            {
                                "source_path": "/environment/location",
                                "candidates": ["street"],
                                "fallback_phrase": "street",
                            },
                        ],
                        "relation_facts": [],
                        "negative_facts": [],
                    }
                )
            )
        return AIMessage(content="{}")


@pytest.mark.asyncio
async def test_workflow_replaces_character_across_turns_without_reparsing_visuals(monkeypatch):
    monkeypatch.setattr(
        "app.services.ai_provider.ai_provider.get_model",
        lambda **kwargs: WorkflowModel(),
    )

    async def query_records(terms, limit=24):
        return [
            {
                "name": term,
                "category": 4 if term in {"hatsune_miku", "moria_luluka"} else 0,
                "post_count": 100,
            }
            for term in terms
        ]

    monkeypatch.setattr(
        "app.agents.prompt_generation.danbooru.query_tag_records", query_records
    )
    agents = runtime_agents()
    workflow = create_prompt_generation_workflow_graph("crew-1", agents)
    thread_id = str(uuid.uuid4())
    first = await workflow.ainvoke(
        build_initial_state(
            "crew-1",
            agents,
            conversation_id=thread_id,
            user_input="create character",
            workflow_inputs={"target_model": "nai_v4", "prompt_strategy": "faithful"},
        ),
        config={"configurable": {"thread_id": thread_id}},
    )
    memory = extract_workflow_memory(first)
    first_answer = first["nodes"]["target_renderer"]["answer"]
    assert "hatsune_miku" in first_answer

    second = await workflow.ainvoke(
        build_initial_state(
            "crew-1",
            agents,
            conversation_id=thread_id,
            user_input="replace character",
            messages=[
                AIMessage(
                    content=first_answer,
                    additional_kwargs={"workflow_memory": memory},
                )
            ],
            workflow_inputs={"target_model": "nai_v4", "prompt_strategy": "faithful"},
        ),
        config={"configurable": {"thread_id": thread_id}},
    )
    answer = second["nodes"]["target_renderer"]["answer"]
    impact = second["nodes"]["scene_document_processor"]["impact_set"]

    assert "moria_luluka" in answer
    assert "hatsune_miku" not in answer
    assert "walking" in answer and "street" in answer
    assert impact["identity_changed"] is True
    assert impact["visual_changed"] is False


def test_extract_workflow_memory_prefers_scene_document_contract():
    document = sample_document(version=3)
    memory = extract_workflow_memory(
        {
            "nodes": {
                "processor": {"scene_document": document},
                "compiler": {"resolved_prompt_ir": {"document_version": 3}},
            }
        }
    )

    assert memory["scene_document"]["version"] == 3
    assert memory["resolved_prompt_ir"]["document_version"] == 3
