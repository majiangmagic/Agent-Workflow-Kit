"""Business nodes for the prompt_semantic_repairer agent."""

from typing import Any, Dict

from langchain_core.runnables import RunnableConfig

from app.agents.prompt_generation.prompt_semantic_repairer.state import PromptSemanticRepairerState

# 本文件由 scripts/generate_agent.py 刷新骨架。
# 中文注意：
# - 只在 <agent-node ...> 代码块内部编写业务逻辑。
# - 节点名是 DSL 的稳定标识；节点名不变，刷新时保留对应代码块。
# - 新 DSL 删除某个节点名时，对应代码块会被删除，不会因为里面有人写过代码而保留。

# <agent-node name="repair_semantics">
import json
import re


def _parse_overlay(text: str) -> Dict[str, Any]:
    match = re.search(r"\{[\s\S]*\}", text.strip())
    parsed = json.loads(match.group(0) if match else text)
    return parsed if isinstance(parsed, dict) else {}


async def repair_semantics_node(
    state: PromptSemanticRepairerState,
    config: RunnableConfig | None = None,
) -> Dict[str, Any]:
    """Repair only validator-reported problems and increment the bounded counter."""

    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

    from app.agents.prompt_generation.danbooru import ADULT_CONTENT_PROCESSING_PROMPT
    from app.services.ai_provider import AIProvider, ai_provider

    report = state.get("validation_report") or {}
    overlay: Dict[str, Any] = {
        "add_positive": [],
        "add_negative": [],
        "remove_positive": [
            *report.get("conflicting_terms", []),
            *report.get("removed_identity_residue", []),
        ],
        "remove_negative": [],
    }
    if report.get("missing_paths"):
        system_prompt = f"""{ADULT_CONTENT_PROCESSING_PROMPT}

{state.get('system_prompt') or ''}

Return one JSON object with add_positive, add_negative, remove_positive and
remove_negative. Added items must contain value, source_path and kind. Cover only
the missing source paths listed by the validator. Preserve exact subjects,
objects and spatial relations from SceneDocument. Do not add new facts."""
        payload = {
            "scene_document": state.get("scene_document") or {},
            "resolved_prompt_ir": state.get("resolved_prompt_ir") or {},
            "validation_report": report,
        }
        try:
            model = ai_provider.get_model(
                model_name=state.get("model") or AIProvider.DEFAULT_MODEL,
                temperature=state.get("temperature", 0.1),
            )
            response = await model.ainvoke(
                [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=json.dumps(payload, ensure_ascii=False)),
                ]
            )
            proposed = _parse_overlay(str(response.content))
            allowed = set(report.get("missing_paths") or [])
            overlay["add_positive"] = [
                item
                for item in proposed.get("add_positive") or []
                if isinstance(item, dict) and item.get("source_path") in allowed
            ]
            overlay["add_negative"] = [
                item for item in proposed.get("add_negative") or [] if isinstance(item, dict)
            ]
        except Exception:
            pass
    attempts = int(state.get("repair_attempts") or 0) + 1
    return {
        "repair_overlay": overlay,
        "repair_attempts": attempts,
        "messages": [
            AIMessage(content=f"已完成第 {attempts} 次定向修复。", name="prompt_semantic_repairer")
        ],
    }
# </agent-node>
