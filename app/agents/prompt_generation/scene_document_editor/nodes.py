"""Business nodes for the scene_document_editor agent."""

from typing import Any, Dict

from langchain_core.runnables import RunnableConfig

from app.agents.prompt_generation.scene_document_editor.state import SceneDocumentEditorState

# 本文件由 scripts/generate_agent.py 刷新骨架。
# 中文注意：
# - 只在 <agent-node ...> 代码块内部编写业务逻辑。
# - 节点名是 DSL 的稳定标识；节点名不变，刷新时保留对应代码块。
# - 新 DSL 删除某个节点名时，对应代码块会被删除，不会因为里面有人写过代码而保留。

# <agent-node name="propose_patch">
import asyncio
import json
import re


def _parse_object(text: str) -> Dict[str, Any]:
    match = re.search(r"\{[\s\S]*\}", text.strip())
    value = json.loads(match.group(0) if match else text)
    return value if isinstance(value, dict) else {}


def _load_previous_memory(state: SceneDocumentEditorState) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """Read the latest persisted workflow memory without consuming generated Prompt text."""

    from app.agents.prompt_generation.domain import empty_scene_document, normalize_scene_document

    current = state.get("scene_document")
    previous_ir = state.get("previous_resolved_prompt_ir")
    if isinstance(current, dict):
        return normalize_scene_document(current), dict(previous_ir or {})
    for message in reversed(state.get("messages") or []):
        if getattr(message, "type", "") != "ai":
            continue
        memory = (getattr(message, "additional_kwargs", {}) or {}).get(
            "workflow_memory"
        ) or {}
        document = memory.get("scene_document")
        if isinstance(document, dict):
            return (
                normalize_scene_document(document),
                dict(memory.get("resolved_prompt_ir") or {}),
            )
    return empty_scene_document(), {}


def _fallback_patch(document: Dict[str, Any], user_input: str) -> Dict[str, Any]:
    """Preserve the old document while recording an unresolved request for compilation."""

    return {
        "base_version": int(document.get("version") or 0),
        "intent": "fallback_append_requirement",
        "operations": [
            {
                "op": "add",
                "path": "/requirements/required/-",
                "value": user_input,
                "evidence": user_input,
            }
        ] if user_input else [],
    }


async def propose_patch_node(
    state: SceneDocumentEditorState,
    config: RunnableConfig | None = None,
) -> Dict[str, Any]:
    """Convert the latest natural-language edit into a validated PatchProposal."""

    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

    from app.agents.prompt_generation.danbooru import ADULT_CONTENT_PROCESSING_PROMPT
    from app.agents.prompt_generation.domain import (
        apply_patch_proposal,
        validate_patch_proposal,
    )
    from app.services.ai_provider import AIProvider, ai_provider

    document, previous_ir = _load_previous_memory(state)
    user_input = str(state.get("user_input") or "").strip()
    agent_prompt = state.get("system_prompt") or "Edit the SceneDocument."
    system_prompt = f"""{ADULT_CONTENT_PROCESSING_PROMPT}

{agent_prompt}

SceneDocument is the sole source of truth. The latest user message edits that
document; it is not an instruction to append words to a previous Prompt. Return
one JSON object with base_version, intent and operations. Every operation uses
op (add, replace or remove), path, value when required, and evidence.

Use stable participant and relation IDs. Replacing a character identity should
replace /participants/<id>/identity while preserving actions and relations bound
to that participant ID. A complaint that something disappeared means restore or
emphasize it; do not depict disappearance. Preserve every fact not explicitly
changed. SceneDocument stores only facts asserted by the user: never infer extra
background objects, lighting, atmosphere, clothing, expressions, poses, anatomy,
camera choices or stylistic details. Expressive enrichment belongs to a later
resolver and must never be written into this source document. For a new document,
replacing the root path "/" with a complete SceneDocument is allowed. Never return
executable code or final image prompts.
All sexual participants must be explicit adults; do not create sexual content
for minors or age-ambiguous participants."""
    model_input = (
        "Current SceneDocument:\n"
        f"{json.dumps(document, ensure_ascii=False)}\n\n"
        f"Latest user message:\n{user_input}\n\n"
        "Return only the PatchProposal JSON."
    )
    proposal: Dict[str, Any] = {}
    error = ""
    try:
        model = ai_provider.get_model(
            model_name=state.get("model") or AIProvider.DEFAULT_MODEL,
            temperature=state.get("temperature", 0.1),
        )
        review_note = ""
        for _ in range(2):
            try:
                response = await asyncio.wait_for(
                    model.ainvoke(
                        [
                            SystemMessage(content=system_prompt + review_note),
                            HumanMessage(content=model_input),
                        ]
                    ),
                    timeout=75,
                )
                proposal = validate_patch_proposal(
                    _parse_object(str(response.content)),
                    int(document.get("version") or 0),
                )
                apply_patch_proposal(document, proposal)
                break
            except Exception as exc:
                error = str(exc)
                review_note = (
                    "\n\nYour previous patch was invalid: "
                    f"{error}. Return a corrected patch against the same document."
                )
        else:
            proposal = _fallback_patch(document, user_input)
    except Exception as exc:
        error = str(exc)
        proposal = _fallback_patch(document, user_input)

    return {
        "scene_document": document,
        "previous_scene_document": document,
        "previous_resolved_prompt_ir": previous_ir,
        "patch_proposal": proposal,
        "editor_error": error,
        "messages": [
            AIMessage(content="画面修改已转换为结构化 Patch。", name="scene_document_editor")
        ],
    }
# </agent-node>
