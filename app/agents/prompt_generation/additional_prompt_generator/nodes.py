"""Business nodes for the additional_prompt_generator agent."""

from typing import Any, Dict

from langchain_core.runnables import RunnableConfig

from app.agents.prompt_generation.additional_prompt_generator.state import AdditionalPromptGeneratorState

# 本文件由 scripts/generate_agent.py 刷新骨架。
# 中文注意：
# - 只在 <agent-node ...> 代码块内部编写业务逻辑。
# - 节点名是 DSL 的稳定标识；节点名不变，刷新时保留对应代码块。
# - 新 DSL 删除某个节点名时，对应代码块会被删除，不会因为里面有人写过代码而保留。

# <agent-node name="generate_additional_prompt">
async def generate_additional_prompt_node(
    state: AdditionalPromptGeneratorState,
    config: RunnableConfig | None = None,
) -> Dict[str, Any]:
    """Generate style, composition, camera, lighting, and effect tags."""

    from langchain_core.messages import AIMessage

    from app.agents.prompt_generation.danbooru import (
        lookup_for_generator,
        verified_tags_from_records,
    )

    terms, records = await lookup_for_generator(state, "additional")
    tags = verified_tags_from_records(records)
    return {
        "additional_prompt": ", ".join(tags),
        "additional_tags": tags,
        "danbooru_tag_records": records,
        "danbooru_search_terms": terms,
        "messages": [
            AIMessage(
                content=f"额外提示词生成完成，采用 {len(tags)} 个 Danbooru 标签。",
                name="additional_prompt_generator",
            )
        ],
    }
# </agent-node>
