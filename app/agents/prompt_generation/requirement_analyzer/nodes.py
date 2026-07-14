"""Business nodes for the prompt_requirement_analyzer agent."""

from typing import Any, Dict

from langchain_core.runnables import RunnableConfig

from app.agents.prompt_generation.requirement_analyzer.state import PromptRequirementAnalyzerState

# 本文件由 scripts/generate_agent.py 刷新骨架。
# 中文注意：
# - 只在 <agent-node ...> 代码块内部编写业务逻辑。
# - 节点名是 DSL 的稳定标识；节点名不变，刷新时保留对应代码块。
# - 新 DSL 删除某个节点名时，对应代码块会被删除，不会因为里面有人写过代码而保留。

# <agent-node name="analyze">
import json
import re


def detect_target_model(text: str) -> str:
    """Detect explicit model requests, defaulting to the NAI tag style."""

    lowered = text.lower()
    if "illustrious" in lowered or "光辉" in text or "光輝" in text:
        return "illustrious"
    if "sdxl" in lowered or "stable diffusion xl" in lowered:
        return "sdxl"
    if "novelai" in lowered or re.search(r"\bnai\b", lowered):
        return "nai"
    if "pony" in lowered:
        return "pony"
    if "flux" in lowered:
        return "flux"
    return "nai"


def strip_target_model_directive(text: str) -> str:
    """Remove UI-injected target-model lines from the semantic request."""

    return re.sub(
        r"^\s*(?:target\s*model|\u76ee\u6807\u6a21\u578b)\s*[:\uff1a]\s*[^\n\r]+\s*",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()


def parse_json_object(text: str) -> Dict[str, Any]:
    match = re.search(r"\{[\s\S]*\}", text.strip())
    data = json.loads(match.group(0) if match else text)
    return data if isinstance(data, dict) else {}


def unique_text_list(*values: Any) -> list[str]:
    """合并字符串或字符串数组，同时保留稳定顺序。"""

    result = []
    seen = set()
    for value in values:
        items = value if isinstance(value, list) else [value]
        for item in items:
            text = str(item or "").strip()
            key = text.casefold()
            if text and key not in seen:
                result.append(text)
                seen.add(key)
    return result


def format_recent_history(messages: list[Any], current_input: str) -> str:
    """Build a compact transcript for resolving follow-up prompt edits."""

    lines = []
    for message in messages[-8:]:
        content = str(getattr(message, "content", "") or "").strip()
        if not content:
            continue
        message_type = getattr(message, "type", "")
        if message_type != "human":
            continue
        lines.append(f"user: {strip_target_model_directive(content)}")
    if not lines or current_input not in lines[-1]:
        lines.append(f"user: {current_input}")
    return "\n".join(lines)


def join_requirement_parts(requirements: Dict[str, Any], fallback: str) -> str:
    """Create the complete request text used by downstream lookup agents."""

    for key in ("resolved_request", "complete_request", "request"):
        value = str(requirements.get(key) or "").strip()
        if value:
            return strip_target_model_directive(value)

    parts = []
    for key in ("character", "scene", "style", "composition", "negative"):
        value = requirements.get(key)
        if isinstance(value, list):
            value = ", ".join(str(item) for item in value if item)
        value = str(value or "").strip()
        if value:
            parts.append(value)
    return strip_target_model_directive("; ".join(parts) or fallback)


async def analyze_node(
    state: PromptRequirementAnalyzerState,
    config: RunnableConfig | None = None,
) -> Dict[str, Any]:
    """Convert the request into a stable contract for parallel generators."""

    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

    from app.agents.prompt_generation.danbooru import ADULT_CONTENT_PROCESSING_PROMPT
    from app.services.ai_provider import AIProvider, ai_provider

    user_input = str(state.get("user_input") or "").strip()
    semantic_user_input = strip_target_model_directive(user_input)
    editor_succeeded = bool(state.get("editor_succeeded"))
    resolved_by_editor = str(state.get("resolved_user_request") or "").strip()
    request_contract = (
        dict(state.get("request_contract") or {}) if editor_succeeded else {}
    )
    request_to_analyze = (
        strip_target_model_directive(resolved_by_editor)
        if editor_succeeded and resolved_by_editor
        else semantic_user_input
    )
    detected_model = detect_target_model(user_input)
    requirements: Dict[str, Any] = {
        "latest_user_input": semantic_user_input,
        "raw_request": request_to_analyze,
        "resolved_request": request_to_analyze,
        "character": "",
        "scene": "",
        "style": "",
        "composition": "",
        "positive_phrases": [],
        "negative_phrases": [],
        "character_tag_candidates": [],
        "scene_tag_candidates": [],
        "additional_tag_candidates": [],
        "required_elements": unique_text_list(
            request_contract.get("required_elements")
        ),
        "forbidden_elements": unique_text_list(
            request_contract.get("forbidden_elements")
        ),
        "spatial_relations": unique_text_list(
            request_contract.get("spatial_relations")
        ),
        "negative": [],
        "target_model": detected_model,
    }
    agent_prompt = state.get("system_prompt") or (
        "Analyze an image generation request. Return one JSON object with keys: "
        "character, scene, style, composition, negative, target_model."
    )
    system_prompt = (
        f"{ADULT_CONTENT_PROCESSING_PROMPT}\n\n{agent_prompt}\n\n"
        "The request contract is the sole source of truth. Do not reinterpret any "
        "conversation history or edit wording. Convert it into one JSON object with "
        "character, scene, style, composition, positive_phrases, negative_phrases, "
        "character_tag_candidates, scene_tag_candidates, additional_tag_candidates, "
        "and target_model. The phrase fields must be arrays of "
        "concise, prompt-ready English visual phrases. Preserve every required "
        "element and spatial relation in positive_phrases. Translate every forbidden "
        "element and negative constraint into negative_phrases. A defect report must "
        "never become positive visual content. Tag candidate fields must contain only "
        "concise Danbooru-style names directly supported by the request. Never infer "
        "unmentioned anatomy, identities, actions, absences, defects, or franchises. "
        "Do not return or rewrite resolved_request."
    )
    analysis_input = (
        "Authoritative request contract:\n"
        f"{json.dumps(request_contract, ensure_ascii=False)}\n\n"
        "Authoritative resolved request:\n"
        f"{request_to_analyze}\n\n"
        "Structure this request as JSON without changing its meaning."
    )
    try:
        model = ai_provider.get_model(
            model_name=state.get("model") or AIProvider.DEFAULT_MODEL,
            temperature=state.get("temperature", 0.2),
        )
        response = await model.ainvoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=analysis_input)]
        )
        parsed = parse_json_object(str(response.content))
        allowed_keys = {
            "character",
            "scene",
            "style",
            "composition",
            "positive_phrases",
            "negative_phrases",
            "character_tag_candidates",
            "scene_tag_candidates",
            "additional_tag_candidates",
            "negative",
            "target_model",
        }
        requirements.update(
            {
                key: value
                for key, value in parsed.items()
                if key in allowed_keys and value is not None
            }
        )
    except Exception:
        pass

    positive_phrases = unique_text_list(requirements.get("positive_phrases"))
    if not positive_phrases:
        positive_phrases = unique_text_list(
            request_contract.get("positive_constraints"),
            request_contract.get("spatial_relations"),
            request_contract.get("required_elements"),
        )
    negative_phrases = unique_text_list(
        requirements.get("negative_phrases"), requirements.get("negative")
    )
    if not negative_phrases:
        negative_phrases = unique_text_list(
            request_contract.get("negative_constraints"),
            request_contract.get("forbidden_elements"),
        )
    requirements["positive_phrases"] = positive_phrases
    requirements["negative_phrases"] = negative_phrases
    requirements["negative"] = requirements["negative_phrases"]
    for key in (
        "character_tag_candidates",
        "scene_tag_candidates",
        "additional_tag_candidates",
    ):
        requirements[key] = unique_text_list(requirements.get(key))
    requirements["latest_user_input"] = semantic_user_input
    requirements["raw_request"] = request_to_analyze
    requirements["resolved_request"] = request_to_analyze
    requirements["request_contract"] = request_contract
    explicit_model = detect_target_model(user_input)
    requirements["target_model"] = explicit_model or "nai"
    return {
        "requirements_json": requirements,
        "messages": [
            AIMessage(
                content=f"需求分析完成，目标模型：{requirements['target_model']}。",
                name="prompt_requirement_analyzer",
            )
        ],
    }
# </agent-node>
