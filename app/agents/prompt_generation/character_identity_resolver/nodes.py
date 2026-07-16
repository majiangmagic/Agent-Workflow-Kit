"""Business nodes for the character_identity_resolver agent."""

from typing import Any, Dict

from langchain_core.runnables import RunnableConfig

from app.agents.prompt_generation.character_identity_resolver.state import CharacterIdentityResolverState

# 本文件由 scripts/generate_agent.py 刷新骨架。
# 中文注意：
# - 只在 <agent-node ...> 代码块内部编写业务逻辑。
# - 节点名是 DSL 的稳定标识；节点名不变，刷新时保留对应代码块。
# - 新 DSL 删除某个节点名时，对应代码块会被删除，不会因为里面有人写过代码而保留。

# <agent-node name="resolve_identities">
import json
import re


def _parse_identities(text: str) -> list[Dict[str, Any]]:
    match = re.search(r"\{[\s\S]*\}", text.strip())
    parsed = json.loads(match.group(0) if match else text)
    values = parsed.get("identities") if isinstance(parsed, dict) else []
    return [item for item in values or [] if isinstance(item, dict)]


def _tag(value: Any) -> str:
    return re.sub(r"\s+", "_", str(value or "").strip().lower())


async def resolve_identities_node(
    state: CharacterIdentityResolverState,
    config: RunnableConfig | None = None,
) -> Dict[str, Any]:
    """Resolve named participants and verify their character-category tags."""

    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

    from app.agents.prompt_generation.danbooru import query_tag_records, unique_text
    from app.services.ai_provider import AIProvider, ai_provider

    document = state.get("scene_document") or {}
    previous_ir = state.get("previous_resolved_prompt_ir") or {}
    impact = state.get("impact_set") or {}
    participants = document.get("participants") or {}
    if not impact.get("identity_changed") and previous_ir.get("identity_terms") is not None:
        return {
            "identity_terms": list(previous_ir.get("identity_terms") or []),
            "identity_tag_records": list(previous_ir.get("identity_tag_records") or []),
            "identity_search_terms": list(previous_ir.get("identity_search_terms") or []),
            "messages": [
                AIMessage(content="角色身份未变化，已复用上一版本解析。", name="character_identity_resolver")
            ],
        }

    named = [
        {
            "participant_id": participant_id,
            "input_name": str((participant.get("identity") or {}).get("input_name") or "").strip(),
        }
        for participant_id, participant in participants.items()
        if str((participant.get("identity") or {}).get("input_name") or "").strip()
    ]
    resolved: list[Dict[str, Any]] = []
    if named:
        system_prompt = (
            f"{state.get('system_prompt') or ''}\n\n"
            "Return one JSON object with identities. Each item must contain "
            "participant_id, input_name, canonical_name, series and "
            "danbooru_tag_candidates. Candidates must be plausible exact Danbooru "
            "character tags, including an unqualified tag when that is the real tag. "
            "Never replace a character with a similar identity. If uncertain, keep "
            "the canonical name useful for lookup and return an empty candidate list."
        )
        try:
            model = ai_provider.get_model(
                model_name=state.get("model") or AIProvider.DEFAULT_MODEL,
                temperature=state.get("temperature", 0.1),
            )
            response = await model.ainvoke(
                [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=json.dumps(named, ensure_ascii=False)),
                ]
            )
            resolved = _parse_identities(str(response.content))
        except Exception:
            resolved = []

    by_id = {str(item.get("participant_id") or ""): item for item in resolved}
    candidates: list[str] = []
    for item in named:
        result = by_id.get(item["participant_id"], {})
        candidates.extend(result.get("danbooru_tag_candidates") or [])
        canonical = str(result.get("canonical_name") or "").strip()
        if canonical:
            candidates.append(canonical)
    candidates = unique_text(candidates, limit=24)
    try:
        records = await query_tag_records(candidates, limit=24)
    except Exception:
        records = []
    character_records = [
        record for record in records if int(record.get("category") or 0) == 4
    ]
    verified = {_tag(record.get("name")): record for record in character_records}
    terms: list[Dict[str, Any]] = []
    for item in named:
        participant_id = item["participant_id"]
        result = by_id.get(participant_id, {})
        item_candidates = unique_text(
            [
                *(result.get("danbooru_tag_candidates") or []),
                result.get("canonical_name"),
            ],
            limit=8,
        )
        selected = next(
            (_tag(value) for value in item_candidates if _tag(value) in verified),
            "",
        )
        if selected:
            value = selected
            kind = "verified_identity_tag"
            provenance = "danbooru"
        else:
            value = str(
                result.get("canonical_name") or item.get("input_name") or ""
            ).strip()
            kind = "identity_phrase"
            provenance = "model_unverified"
        if value:
            terms.append(
                {
                    "value": value,
                    "kind": kind,
                    "polarity": "positive",
                    "source_path": f"/participants/{participant_id}/identity",
                    "participant_id": participant_id,
                    "provenance": provenance,
                }
            )
    return {
        "identity_terms": terms,
        "identity_tag_records": character_records,
        "identity_search_terms": candidates,
        "messages": [
            AIMessage(
                content=f"已解析 {len(named)} 个具名角色，验证 {len(character_records)} 个角色标签。",
                name="character_identity_resolver",
            )
        ],
    }
# </agent-node>
