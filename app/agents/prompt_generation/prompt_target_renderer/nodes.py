"""Business nodes for the prompt_target_renderer agent."""

from typing import Any, Dict

from langchain_core.runnables import RunnableConfig

from app.agents.prompt_generation.prompt_target_renderer.state import PromptTargetRendererState

# 本文件由 scripts/generate_agent.py 刷新骨架。
# 中文注意：
# - 只在 <agent-node ...> 代码块内部编写业务逻辑。
# - 节点名是 DSL 的稳定标识；节点名不变，刷新时保留对应代码块。
# - 新 DSL 删除某个节点名时，对应代码块会被删除，不会因为里面有人写过代码而保留。

# <agent-node name="render_prompt">
MODEL_ALIASES = {
    "nai": "nai_v4",
    "novelai": "nai_v4",
    "nai4": "nai_v4",
    "nai v4": "nai_v4",
    "nai_v4": "nai_v4",
    "nai3": "nai_v3",
    "nai v3": "nai_v3",
    "nai_v3": "nai_v3",
    "stable diffusion xl": "sdxl",
    "光辉": "illustrious",
}

MODEL_DEFAULTS = {
    "nai_v4": {
        "positive": ["masterpiece", "best quality", "very aesthetic"],
        "negative": ["lowres", "bad anatomy", "bad hands", "text", "error"],
    },
    "nai_v3": {
        "positive": ["masterpiece", "best quality", "very aesthetic"],
        "negative": ["lowres", "bad anatomy", "bad hands", "text", "error"],
    },
    "sdxl": {
        "positive": ["high quality", "highly detailed"],
        "negative": ["low quality", "blurry", "distorted", "text", "watermark"],
    },
    "illustrious": {
        "positive": ["masterpiece", "best quality", "newest", "very aesthetic"],
        "negative": ["lowres", "worst quality", "bad anatomy", "text", "watermark"],
    },
    "pony": {
        "positive": ["score_9", "score_8_up", "score_7_up"],
        "negative": ["score_4", "score_3", "score_2", "score_1"],
    },
    "flux": {"positive": [], "negative": []},
}


def _unique(values: Any) -> list[str]:
    result = []
    seen = set()
    for value in values:
        text = str(value or "").strip()
        key = text.casefold()
        if text and key not in seen:
            result.append(text)
            seen.add(key)
    return result


def _model(value: Any) -> str:
    key = str(value or "nai_v4").strip().lower()
    return MODEL_ALIASES.get(key, key if key in MODEL_DEFAULTS else "nai_v4")


def render_prompt_node(
    state: PromptTargetRendererState,
    config: RunnableConfig | None = None,
) -> Dict[str, Any]:
    """Render PromptIR for one target model without semantic reinterpretation."""

    from langchain_core.messages import AIMessage

    workflow_inputs = state.get("workflow_inputs") or {}
    target_model = _model(workflow_inputs.get("target_model") or state.get("target_model"))
    prompt_ir = state.get("resolved_prompt_ir") or {}
    positive_entries = prompt_ir.get("positive_terms") or []
    if target_model == "nai_v3":
        positive_entries = [
            item
            for item in positive_entries
            if str(item.get("kind") or "").startswith("verified")
            or item.get("kind") == "verified_tag"
        ]
    elif target_model in {"sdxl", "flux"}:
        positive_entries = sorted(
            positive_entries,
            key=lambda item: 0 if "phrase" in str(item.get("kind") or "") else 1,
        )
    positive_terms = _unique(
        [
            *MODEL_DEFAULTS[target_model]["positive"],
            *[item.get("value") for item in positive_entries],
        ]
    )
    negative_terms = _unique(
        [
            *MODEL_DEFAULTS[target_model]["negative"],
            *[
                item.get("value")
                for item in prompt_ir.get("compiled_negative_terms") or []
            ],
        ]
    )
    positive = (
        ". ".join(positive_terms) if target_model == "flux" else ", ".join(positive_terms)
    )
    negative = ", ".join(negative_terms)
    display = {
        "nai_v4": "NAI V4",
        "nai_v3": "NAI V3",
        "sdxl": "SDXL",
        "illustrious": "Illustrious",
        "pony": "Pony",
        "flux": "Flux",
    }.get(target_model, target_model.upper())
    records = prompt_ir.get("danbooru_tag_records") or []
    formatted = (
        f"目标模型：{display}\n\n"
        f"正向提示词\n{positive or '未找到可用提示项'}\n\n"
        f"负向提示词\n{negative or '无'}\n\n"
        f"Danbooru 来源标签：{len(records)} 个"
    )
    final_output = {
        "target_model": target_model,
        "positive_prompt": positive,
        "negative_prompt": negative,
        "scene_document_version": (state.get("scene_document") or {}).get("version", 0),
        "resolved_prompt_ir": prompt_ir,
        "validation_report": state.get("validation_report") or {},
        "danbooru_tag_records": records,
    }
    return {
        "target_model": target_model,
        "formatted_prompt": formatted,
        "answer": formatted,
        "final_output": final_output,
        "messages": [AIMessage(content=formatted, name="prompt_target_renderer")],
    }
# </agent-node>
