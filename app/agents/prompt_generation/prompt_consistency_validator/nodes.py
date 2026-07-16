"""Business nodes for the prompt_consistency_validator agent."""

from typing import Any, Dict

from langchain_core.runnables import RunnableConfig

from app.agents.prompt_generation.prompt_consistency_validator.state import PromptConsistencyValidatorState

# 本文件由 scripts/generate_agent.py 刷新骨架。
# 中文注意：
# - 只在 <agent-node ...> 代码块内部编写业务逻辑。
# - 节点名是 DSL 的稳定标识；节点名不变，刷新时保留对应代码块。
# - 新 DSL 删除某个节点名时，对应代码块会被删除，不会因为里面有人写过代码而保留。

# <agent-node name="validate_prompt">
def _term_key(value: Any) -> str:
    return " ".join(str(value or "").strip().casefold().replace("_", " ").split())


def validate_prompt_node(
    state: PromptConsistencyValidatorState,
    config: RunnableConfig | None = None,
) -> Dict[str, Any]:
    """Validate coverage, polarity and removed-identity invariants."""

    from langchain_core.messages import AIMessage

    from app.agents.prompt_generation.domain import collect_required_paths

    document = state.get("scene_document") or {}
    prompt_ir = state.get("resolved_prompt_ir") or {}
    positive = prompt_ir.get("positive_terms") or []
    negative = prompt_ir.get("compiled_negative_terms") or []
    positive_keys = {_term_key(item.get("value")) for item in positive if isinstance(item, dict)}
    negative_keys = {_term_key(item.get("value")) for item in negative if isinstance(item, dict)}
    conflicts = sorted(key for key in positive_keys & negative_keys if key)
    covered = set(prompt_ir.get("covered_paths") or [])
    missing_paths = [path for path in collect_required_paths(document) if path not in covered]
    removed = [
        _term_key(value)
        for value in (state.get("impact_set") or {}).get("removed_identity_terms") or []
        if value
    ]
    residual_terms = [
        item.get("value")
        for item in positive
        if isinstance(item, dict)
        and any(
            old == _term_key(item.get("value")) or old in _term_key(item.get("value"))
            for old in removed
        )
    ]
    issues = []
    if missing_paths:
        issues.append("missing_required_paths")
    if conflicts:
        issues.append("positive_negative_conflict")
    if residual_terms:
        issues.append("removed_identity_residue")
    report = {
        "valid": not issues,
        "issues": issues,
        "missing_paths": missing_paths,
        "conflicting_terms": conflicts,
        "removed_identity_residue": residual_terms,
        "required_path_count": len(collect_required_paths(document)),
        "covered_path_count": len(covered),
    }
    return {
        "validation_report": report,
        "needs_repair": bool(issues),
        "messages": [
            AIMessage(
                content="Prompt IR 一致性检查通过。" if not issues else f"发现 {len(issues)} 类一致性问题。",
                name="prompt_consistency_validator",
            )
        ],
    }
# </agent-node>
