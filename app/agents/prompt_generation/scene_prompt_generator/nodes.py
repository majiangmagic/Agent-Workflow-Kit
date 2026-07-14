"""Business nodes for the scene_prompt_generator agent."""

from typing import Any, Dict

from langchain_core.runnables import RunnableConfig

from app.agents.prompt_generation.scene_prompt_generator.state import ScenePromptGeneratorState

# 本文件由 scripts/generate_agent.py 刷新骨架。
# 中文注意：
# - 只在 <agent-node ...> 代码块内部编写业务逻辑。
# - 节点名是 DSL 的稳定标识；节点名不变，刷新时保留对应代码块。
# - 新 DSL 删除某个节点名时，对应代码块会被删除，不会因为里面有人写过代码而保留。

# <agent-node name="generate_scene_prompt">
async def generate_scene_prompt_node(
    state: ScenePromptGeneratorState,
    config: RunnableConfig | None = None,
) -> Dict[str, Any]:
    """Generate scene tags and include their Danbooru provenance."""

    from langchain_core.messages import AIMessage

    from app.agents.prompt_generation.danbooru import (
        lookup_for_generator,
        verified_tags_from_records,
    )

    terms, records = await lookup_for_generator(state, "scene")
    tags = verified_tags_from_records(records)
    return {
        "scene_prompt": ", ".join(tags),
        "scene_tags": tags,
        "danbooru_tag_records": records,
        "danbooru_search_terms": terms,
        "messages": [
            AIMessage(
                content=f"场景提示词生成完成，采用 {len(tags)} 个 Danbooru 标签。",
                name="scene_prompt_generator",
            )
        ],
    }
# </agent-node>
