"""Business nodes for the prompt_aggregator agent."""

from typing import Any, Dict

from langchain_core.runnables import RunnableConfig

from app.agents.prompt_generation.prompt_aggregator.state import PromptAggregatorState

# 本文件由 scripts/generate_agent.py 刷新骨架。
# 中文注意：
# - 只在 <agent-node ...> 代码块内部编写业务逻辑。
# - 节点名是 DSL 的稳定标识；节点名不变，刷新时保留对应代码块。
# - 新 DSL 删除某个节点名时，对应代码块会被删除，不会因为里面有人写过代码而保留。

# <agent-node name="aggregate_prompt">
from typing import Iterable, List
import re


def unique_terms(values: Iterable[Any]) -> List[str]:
    result: List[str] = []
    seen = set()
    for value in values:
        for raw_term in str(value or "").split(","):
            term = raw_term.strip()
            key = term.lower()
            if not term or key in seen:
                continue
            result.append(term)
            seen.add(key)
    return result


def unique_records(records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    result = []
    seen = set()
    for record in records:
        name = str(record.get("name") or "")
        if not name or name in seen:
            continue
        result.append(record)
        seen.add(name)
    return result


def normalized_term(value: Any) -> str:
    return " ".join(str(value or "").strip().casefold().replace("_", " ").split())


def normalize_negative_phrase(value: Any) -> str:
    """负向 Prompt 表达不再携带 no/不要 等否定词，避免双重否定。"""

    text = str(value or "").strip()
    text = re.sub(
        r"^(?:no|not|without|avoid|avoiding|exclude|excluding)\s+",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"^(?:禁止|不要|避免|不得|不能)\s*", "", text)
    return text.strip(" ,，。")


def split_by_polarity(
    positive_values: Iterable[Any],
    negative_values: Iterable[Any],
) -> tuple[List[str], List[str], List[str]]:
    """隔离显式否定描述，避免它们作为正向画面内容输出。"""

    negative = unique_terms(
        normalize_negative_phrase(value) for value in negative_values
    )
    negative_keys = {normalized_term(value) for value in negative}
    positive = []
    moved = []
    negative_prefixes = (
        "no ",
        "not ",
        "without ",
        "avoid ",
        "exclude ",
        "禁止",
        "不要",
        "避免",
        "不得",
        "不能",
    )
    for value in unique_terms(positive_values):
        normalized = normalized_term(value)
        if normalized in negative_keys:
            continue
        if normalized.startswith(negative_prefixes):
            moved.append(normalize_negative_phrase(value))
            continue
        positive.append(value)
    return positive, unique_terms([*negative, *moved]), moved


def aggregate_prompt_node(
    state: PromptAggregatorState,
    config: RunnableConfig | None = None,
) -> Dict[str, Any]:
    """Merge parallel outputs without changing model-specific syntax."""

    from langchain_core.messages import AIMessage

    sections = {
        "character": unique_terms(state.get("character_tags") or []),
        "scene": unique_terms(state.get("scene_tags") or []),
        "additional": unique_terms(state.get("additional_tags") or []),
    }
    requirements = state.get("requirements_json") or {}
    verified_tags = unique_terms(
        [*sections["character"], *sections["scene"], *sections["additional"]]
    )
    positive_phrases, negative_phrases, moved_negative_phrases = split_by_polarity(
        requirements.get("positive_phrases") or [],
        requirements.get("negative_phrases") or requirements.get("negative") or [],
    )
    draft_terms = unique_terms([*verified_tags, *positive_phrases])
    records = unique_records(state.get("danbooru_tag_records") or [])
    verified_keys = {normalized_term(record.get("name")) for record in records}
    search_terms = unique_terms(state.get("danbooru_search_terms") or [])
    unverified_candidates = [
        term for term in search_terms if normalized_term(term) not in verified_keys
    ]
    consistency_report = {
        "required_elements": requirements.get("required_elements") or [],
        "forbidden_elements": requirements.get("forbidden_elements") or [],
        "spatial_relations": requirements.get("spatial_relations") or [],
        "moved_negative_phrases": moved_negative_phrases,
        "unverified_candidates_excluded": unverified_candidates,
        "verified_tag_count": len(verified_tags),
        "descriptive_phrase_count": len(positive_phrases),
    }
    sections["descriptive_phrases"] = positive_phrases
    sections["negative_constraints"] = negative_phrases
    return {
        "draft_prompt": ", ".join(draft_terms),
        "negative_prompt": ", ".join(negative_phrases),
        "prompt_sections": sections,
        "danbooru_tag_records": records,
        "consistency_report": consistency_report,
        "messages": [
            AIMessage(
                content=f"提示词汇总完成，共 {len(draft_terms)} 个去重标签。",
                name="prompt_aggregator",
            )
        ],
    }
# </agent-node>
