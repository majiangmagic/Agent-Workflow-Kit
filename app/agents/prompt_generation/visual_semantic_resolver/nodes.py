"""Business nodes for the visual_semantic_resolver agent."""

from typing import Any, Dict

from langchain_core.runnables import RunnableConfig

from app.agents.prompt_generation.visual_semantic_resolver.state import VisualSemanticResolverState

# 本文件由 scripts/generate_agent.py 刷新骨架。
# 中文注意：
# - 只在 <agent-node ...> 代码块内部编写业务逻辑。
# - 节点名是 DSL 的稳定标识；节点名不变，刷新时保留对应代码块。
# - 新 DSL 删除某个节点名时，对应代码块会被删除，不会因为里面有人写过代码而保留。

# <agent-node name="resolve_visual_semantics">
import json
import re


def _parse_object(text: str) -> Dict[str, Any]:
    match = re.search(r"\{[\s\S]*\}", text.strip())
    parsed = json.loads(match.group(0) if match else text)
    return parsed if isinstance(parsed, dict) else {}


def _normalized(value: Any) -> str:
    return re.sub(r"\s+", "_", str(value or "").strip().lower())


def _facts(value: Any) -> list[Dict[str, Any]]:
    return [item for item in value or [] if isinstance(item, dict)]


def _fallback_relation_terms(document: Dict[str, Any]) -> list[Dict[str, Any]]:
    """Keep explicit facts usable when semantic model output is unavailable."""

    terms = []
    for relation_id, relation in (document.get("relations") or {}).items():
        parts = [
            relation.get("subject"),
            relation.get("predicate"),
            relation.get("object"),
            relation.get("instrument"),
            relation.get("source"),
            relation.get("body_region"),
            *(relation.get("details") or []),
        ]
        phrase = " ".join(str(value) for value in parts if value).strip()
        if phrase:
            terms.append(
                {
                    "value": phrase,
                    "kind": "relation_phrase",
                    "polarity": "positive",
                    "source_path": f"/relations/{relation_id}",
                    "provenance": "deterministic_fallback",
                    "inferred": False,
                }
            )
    for key in ("positive", "required"):
        for index, value in enumerate((document.get("requirements") or {}).get(key) or []):
            terms.append(
                {
                    "value": value,
                    "kind": "descriptive_phrase",
                    "polarity": "positive",
                    "source_path": f"/requirements/{key}/{index}",
                    "provenance": "document",
                    "inferred": False,
                }
            )
    return terms


async def resolve_visual_semantics_node(
    state: VisualSemanticResolverState,
    config: RunnableConfig | None = None,
) -> Dict[str, Any]:
    """Resolve non-identity facts into verified tags and relation-preserving phrases."""

    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

    from app.agents.prompt_generation.danbooru import (
        ADULT_CONTENT_PROCESSING_PROMPT,
        query_tag_records,
        unique_text,
    )
    from app.services.ai_provider import AIProvider, ai_provider

    document = state.get("scene_document") or {}
    previous_ir = state.get("previous_resolved_prompt_ir") or {}
    impact = state.get("impact_set") or {}
    if not impact.get("visual_changed") and previous_ir.get("atomic_terms") is not None:
        return {
            "atomic_terms": list(previous_ir.get("atomic_terms") or []),
            "relation_terms": list(previous_ir.get("relation_terms") or []),
            "negative_terms": list(previous_ir.get("negative_terms") or []),
            "visual_tag_records": list(previous_ir.get("visual_tag_records") or []),
            "visual_search_terms": list(previous_ir.get("visual_search_terms") or []),
            "messages": [
                AIMessage(content="视觉事实未变化，已复用上一版本解析。", name="visual_semantic_resolver")
            ],
        }

    workflow_inputs = state.get("workflow_inputs") or {}
    strategy = str(workflow_inputs.get("prompt_strategy") or "expressive")
    system_prompt = f"""{ADULT_CONTENT_PROCESSING_PROMPT}

{state.get('system_prompt') or ''}

Return one JSON object with atomic_facts, relation_facts and negative_facts.
Every fact must contain source_path. atomic_facts contain candidates (plausible
exact Danbooru tag names) and fallback_phrase. relation_facts contain phrase.
negative_facts contain phrase. Do not emit character identity tags; identity is
resolved by another component. Preserve subjects, objects, body regions, sources,
connections and spatial direction in relation phrases. A complaint about the last
render is a correction, not positive depicted content.

Strategy is {strategy}. In faithful mode emit only explicit document facts. In
expressive mode you may add at most 8 useful visual refinements, mark them
inferred=true, and never add identities, participants, core actions or relations.
Use concise English phrases suitable for image prompting."""
    parsed: Dict[str, Any] = {}
    try:
        model = ai_provider.get_model(
            model_name=state.get("model") or AIProvider.DEFAULT_MODEL,
            temperature=state.get("temperature", 0.2),
        )
        response = await model.ainvoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=json.dumps(document, ensure_ascii=False)),
            ]
        )
        parsed = _parse_object(str(response.content))
    except Exception:
        parsed = {}

    atomic_facts = _facts(parsed.get("atomic_facts"))
    candidates = unique_text(
        [
            candidate
            for fact in atomic_facts
            for candidate in (fact.get("candidates") or [])
        ],
        limit=40,
    )
    try:
        records = await query_tag_records(candidates, limit=40)
    except Exception:
        records = []
    verified = {_normalized(record.get("name")): record for record in records}
    atomic_terms: list[Dict[str, Any]] = []
    for fact in atomic_facts:
        source_path = str(fact.get("source_path") or "").strip()
        matched = [
            _normalized(candidate)
            for candidate in fact.get("candidates") or []
            if _normalized(candidate) in verified
        ]
        if matched:
            for value in matched:
                atomic_terms.append(
                    {
                        "value": value,
                        "kind": "verified_tag",
                        "polarity": "positive",
                        "source_path": source_path,
                        "provenance": "danbooru",
                        "inferred": bool(fact.get("inferred")),
                    }
                )
        else:
            fallback = str(fact.get("fallback_phrase") or "").strip()
            if fallback:
                atomic_terms.append(
                    {
                        "value": fallback,
                        "kind": "descriptive_phrase",
                        "polarity": "positive",
                        "source_path": source_path,
                        "provenance": "model_fallback",
                        "inferred": bool(fact.get("inferred")),
                    }
                )

    relation_terms = [
        {
            "value": str(fact.get("phrase") or "").strip(),
            "kind": "relation_phrase",
            "polarity": "positive",
            "source_path": str(fact.get("source_path") or "").strip(),
            "provenance": "model",
            "inferred": bool(fact.get("inferred")),
        }
        for fact in _facts(parsed.get("relation_facts"))
        if str(fact.get("phrase") or "").strip()
    ]
    if not relation_terms:
        relation_terms = _fallback_relation_terms(document)
    negative_terms = [
        {
            "value": str(fact.get("phrase") or "").strip(),
            "kind": "negative_phrase",
            "polarity": "negative",
            "source_path": str(fact.get("source_path") or "").strip(),
            "provenance": "model",
            "inferred": False,
        }
        for fact in _facts(parsed.get("negative_facts"))
        if str(fact.get("phrase") or "").strip()
    ]
    if not negative_terms:
        negative_terms = [
            {
                "value": value,
                "kind": "negative_phrase",
                "polarity": "negative",
                "source_path": f"/requirements/{key}/{index}",
                "provenance": "document",
                "inferred": False,
            }
            for key in ("negative", "forbidden")
            for index, value in enumerate((document.get("requirements") or {}).get(key) or [])
        ]
    return {
        "atomic_terms": atomic_terms,
        "relation_terms": relation_terms,
        "negative_terms": negative_terms,
        "visual_tag_records": records,
        "visual_search_terms": candidates,
        "messages": [
            AIMessage(
                content=f"已生成 {len(atomic_terms)} 个原子项和 {len(relation_terms)} 个关系项。",
                name="visual_semantic_resolver",
            )
        ],
    }
# </agent-node>
