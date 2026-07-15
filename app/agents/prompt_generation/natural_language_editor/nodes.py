"""Business nodes for the natural_language_editor agent."""

from typing import Any, Dict

from langchain_core.runnables import RunnableConfig

from app.agents.prompt_generation.natural_language_editor.state import NaturalLanguageEditorState

# 本文件由 scripts/generate_agent.py 刷新骨架。
# 中文注意：
# - 只在 <agent-node ...> 代码块内部编写业务逻辑。
# - 节点名是 DSL 的稳定标识；节点名不变，刷新时保留对应代码块。
# - 新 DSL 删除某个节点名时，对应代码块会被删除，不会因为里面有人写过代码而保留。

# <agent-node name="resolve">
# 中文注意：
# 1. 节点名 "resolve" 是 DSL 的稳定标识，不要随手改名。
# 2. 只要 DSL 里还保留这个节点名，刷新骨架时会保留本代码块里的业务逻辑。
# 3. 如果新 DSL 删除了这个节点名，生成器会删除整个代码块，即使里面写过业务代码。
import json
import re
import asyncio


def _strip_ui_directives(text: str) -> str:
    """去掉前端附加的模型选择行，避免它干扰对话意图判断。"""

    return re.sub(
        r"^\s*(?:target\s*model|目标模型)\s*[:：]\s*[^\n\r]+\s*",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()


def _user_transcript(messages: list[Any], latest_input: str) -> str:
    """仅保留用户原话；生成出的 Prompt 不是用户意图，不应回灌。"""

    turns = []
    for message in messages[-12:]:
        if getattr(message, "type", "") != "human":
            continue
        content = _strip_ui_directives(
            str(getattr(message, "content", "") or "").strip()
        )
        if content:
            turns.append(content)
    if latest_input and (not turns or turns[-1] != latest_input):
        turns.append(latest_input)
    return "\n".join(
        f"第{index}轮用户消息：{content}"
        for index, content in enumerate(turns, start=1)
    )


def _parse_object(text: str) -> Dict[str, Any]:
    match = re.search(r"\{[\s\S]*\}", text.strip())
    parsed = json.loads(match.group(0) if match else text)
    return parsed if isinstance(parsed, dict) else {}


def _text_list(value: Any) -> list[str]:
    """规范化模型返回的字符串数组，不对具体语义做预设映射。"""

    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        return []
    result = []
    seen = set()
    for item in value:
        text = str(item or "").strip()
        key = text.casefold()
        if text and key not in seen:
            result.append(text)
            seen.add(key)
    return result


def _previous_contract(state: NaturalLanguageEditorState) -> Dict[str, Any]:
    """优先读取 checkpoint，其次读取上一轮助手消息持久化的工作流记忆。"""

    current = state.get("request_contract")
    if isinstance(current, dict) and current.get("resolved_request"):
        return dict(current)
    for message in reversed(state.get("messages") or []):
        if getattr(message, "type", "") != "ai":
            continue
        extra = getattr(message, "additional_kwargs", {}) or {}
        memory = extra.get("workflow_memory") or {}
        contract = memory.get("request_contract")
        if isinstance(contract, dict) and contract.get("resolved_request"):
            return dict(contract)
    return {}


def _normalize_contract(parsed: Dict[str, Any], fallback: str) -> Dict[str, Any]:
    raw = parsed.get("request_contract")
    contract = dict(raw) if isinstance(raw, dict) else {}
    resolved = str(
        contract.get("resolved_request")
        or parsed.get("resolved_user_request")
        or fallback
    ).strip()
    return {
        "resolved_request": resolved,
        "required_elements": _text_list(contract.get("required_elements")),
        "forbidden_elements": _text_list(contract.get("forbidden_elements")),
        "spatial_relations": _text_list(contract.get("spatial_relations")),
        "positive_constraints": _text_list(contract.get("positive_constraints")),
        "negative_constraints": _text_list(contract.get("negative_constraints")),
    }


def _operation_changes_item(item: str, operations: list[Any]) -> bool:
    """只有显式删除或替换操作才能解除上一轮已经存在的约束锚点。"""

    item_key = item.casefold().strip()
    for operation in operations:
        if not isinstance(operation, dict):
            continue
        op = str(operation.get("op") or "").casefold().strip()
        if op not in {"remove", "delete", "exclude", "replace"}:
            continue
        if op == "replace":
            return True
        for operand in (operation.get("target"), operation.get("value")):
            operand_key = str(operand or "").casefold().strip()
            if operand_key and (
                operand_key in item_key or item_key in operand_key
            ):
                return True
    return False


def _inherit_contract_anchors(
    previous: Dict[str, Any],
    current: Dict[str, Any],
    operations: list[Any],
) -> Dict[str, Any]:
    """合并跨轮锚点，防止模型在后续纠错时无意丢失既有要求。"""

    merged = dict(current)
    for key in (
        "required_elements",
        "forbidden_elements",
        "spatial_relations",
        "positive_constraints",
        "negative_constraints",
    ):
        inherited = [
            item
            for item in _text_list(previous.get(key))
            if not _operation_changes_item(item, operations)
        ]
        merged[key] = _text_list([*inherited, *_text_list(current.get(key))])
    resolved = str(merged.get("resolved_request") or "").strip()
    suffixes = []
    for label, key in (
        ("必须保留", "required_elements"),
        ("禁止出现", "forbidden_elements"),
        ("关系约束", "spatial_relations"),
    ):
        missing = [item for item in merged[key] if item not in resolved]
        if missing:
            suffixes.append(f"{label}：{'；'.join(missing)}")
    if suffixes:
        resolved = f"{resolved.rstrip('。')}。{'。'.join(suffixes)}。"
    merged["resolved_request"] = resolved
    return merged


async def resolve_node(
    state: NaturalLanguageEditorState,
    config: RunnableConfig | None = None,
) -> Dict[str, Any]:
    """把自然口语变更应用到上下文，输出完整且与领域无关的当前请求。"""

    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

    from app.agents.prompt_generation.danbooru import ADULT_CONTENT_PROCESSING_PROMPT
    from app.services.ai_provider import AIProvider, ai_provider

    latest_input = _strip_ui_directives(str(state.get("user_input") or "").strip())
    previous_contract = _previous_contract(state)
    transcript = _user_transcript(state.get("messages") or [], latest_input)
    agent_prompt = state.get("system_prompt") or (
        "理解自然语言中的省略、指代和修改，并维护完整的当前请求。"
    )
    system_prompt = (
        f"{ADULT_CONTENT_PROCESSING_PROMPT}\n\n{agent_prompt}\n\n"
        "你位于业务分析之前，只维护对话中的请求状态，不生成提示词标签。根据上下文"
        "理解最新消息实际执行的言语行为，包括新建、补充、删除、替换、恢复、强调、"
        "确认、询问和对上次结果的缺陷报告。用户描述某元素错误、缺失、仍然存在或"
        "效果不对时，这是修正反馈，不是要求把‘错误、缺失、仍然存在’画进图里。"
        "必须将期望保留的内容放入 required_elements，将明确不要的内容放入"
        "forbidden_elements 或 negative_constraints，将来源、连接、位置等关系放入"
        "spatial_relations。保留未被本轮明确修改的既有要求，不得虚构新细节，也不得"
        "使用针对具体短语、角色或标签的映射。\n"
        "只返回一个 JSON 对象，包含 turn_intent、edit_operations、"
        "resolved_user_request 和 request_contract。edit_operations 每项使用"
        "op、target、value、evidence。request_contract 必须包含 resolved_request、"
        "required_elements、forbidden_elements、spatial_relations、"
        "positive_constraints、negative_constraints；后五项均为字符串数组。"
    )
    model_input = (
        "上次规范化请求契约（可能为空）：\n"
        f"{json.dumps(previous_contract, ensure_ascii=False)}\n\n"
        f"按时间排列的用户消息：\n{transcript}\n\n"
        f"最新用户消息：\n{latest_input}\n\n"
        "请应用最新一轮变更并输出 JSON。"
    )

    result: Dict[str, Any] = {
        "turn_intent": "unresolved",
        "edit_operations": [],
        "request_contract": {
            "resolved_request": latest_input,
            "required_elements": [],
            "forbidden_elements": [],
            "spatial_relations": [],
            "positive_constraints": [],
            "negative_constraints": [],
        },
        "resolved_user_request": latest_input,
        "editor_succeeded": False,
    }
    try:
        configured_model = state.get("model") or AIProvider.DEFAULT_MODEL

        async def invoke_editor(model_name: str, review_note: str = "") -> Dict[str, Any]:
            model = ai_provider.get_model(
                model_name=model_name,
                temperature=state.get("temperature", 0.1),
            )
            response = await asyncio.wait_for(
                model.ainvoke(
                    [
                        SystemMessage(content=f"{system_prompt}\n{review_note}"),
                        HumanMessage(content=model_input),
                    ]
                ),
                timeout=75,
            )
            return _parse_object(str(response.content))

        parsed = await invoke_editor(configured_model)
        contract = _normalize_contract(parsed, latest_input)
        resolved_request = contract["resolved_request"]
        if resolved_request:
            operations = parsed.get("edit_operations")
            operations = operations if isinstance(operations, list) else []
            destructive_edit = any(
                _operation_changes_item(item, operations)
                for key in ("required_elements", "forbidden_elements", "spatial_relations")
                for item in _text_list(previous_contract.get(key))
            )
            if destructive_edit and configured_model != AIProvider.SUPERVISOR_MODEL:
                reviewed = await invoke_editor(
                    AIProvider.SUPERVISOR_MODEL,
                    "A faster model proposed removing or replacing an established "
                    "constraint. Re-evaluate the latest utterance carefully. Distinguish "
                    "an explicit command to remove content from a report that the last "
                    "generated result accidentally omitted or misplaced content. Only an "
                    "unambiguous user instruction may authorize a destructive edit.",
                )
                reviewed_contract = _normalize_contract(reviewed, latest_input)
                if reviewed_contract["resolved_request"]:
                    parsed = reviewed
                    contract = reviewed_contract
                    reviewed_operations = reviewed.get("edit_operations")
                    operations = (
                        reviewed_operations
                        if isinstance(reviewed_operations, list)
                        else []
                    )
            contract = _inherit_contract_anchors(
                previous_contract,
                contract,
                operations,
            )
            resolved_request = contract["resolved_request"]
            result.update(
                {
                    "turn_intent": str(parsed.get("turn_intent") or "edit").strip(),
                    "edit_operations": operations,
                    "request_contract": contract,
                    "resolved_user_request": resolved_request,
                    "editor_succeeded": True,
                }
            )
    except Exception:
        # 下游需求分析器仍能用原始消息历史兜底，不让临时模型故障破坏整条链路。
        pass

    return {
        **result,
        "messages": [
            AIMessage(content="自然语言编辑完成。", name="natural_language_editor")
        ],
    }
# </agent-node>
