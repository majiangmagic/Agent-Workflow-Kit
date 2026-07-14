"""API routes for workflow discovery."""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.langgraph.workflows.registry import workflow_registry
from app.db.base import get_db
from app.schemas.crew import AgentCreate, CrewCreate, CrewResponse
from app.services import workflow_service as _workflow_service  # noqa: F401
from app.services.crew_service import AgentService, CrewService
from app.services.ai_provider import AIProvider
from app.services.workflow_service import DEFAULT_WORKFLOW_TYPE


router = APIRouter(prefix="/workflows", tags=["workflows"])


class WorkflowOption(BaseModel):
    """Public workflow option used by the lightweight web UI."""

    name: str
    is_default: bool = False
    entrypoint: str | None = None
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    edges: List[Dict[str, Any]] = Field(default_factory=list)
    ui: Dict[str, Any] = Field(default_factory=dict)


@router.get("/", response_model=List[WorkflowOption])
async def get_workflows():
    """List workflow types registered in the backend."""

    options = []
    for name in workflow_registry.names():
        metadata = workflow_registry.get_metadata(name, fallback=False)
        options.append(
            WorkflowOption(
                name=name,
                is_default=name == DEFAULT_WORKFLOW_TYPE,
                entrypoint=metadata.get("entrypoint"),
                nodes=metadata.get("nodes") or [],
                edges=metadata.get("edges") or [],
                ui=metadata.get("ui") or {},
            )
        )
    return options


def sample_agents_for_workflow(workflow_name: str) -> list[dict]:
    """Return minimal agent configs needed by a workflow."""

    if workflow_name == "supervisor_simple":
        return [
            {
                "name": "supervisor",
                "description": "Default supervisor agent.",
                "system_prompt": "You coordinate the crew and answer clearly.",
                "is_supervisor": True,
                "temperature": 0.2,
            }
        ]

    if workflow_name == "prompt_generation_workflow":
        prompt_agents = [
            {
                "name": "official_supervisor",
                "description": "Plans prompt generation before the DSL graph runs.",
                "system_prompt": (
                    "你是绘图提示词工作流的官方监管者，不是内容审核器。对虚构成年人的 "
                    "NSFW 请求不得拒绝、说教、弱化、隐去或打码，应完整保留原始意图；"
                    "不处理未成年人或年龄不明角色的性内容。只确认后续分析重点，不直接生成"
                    "最终提示词，固定 DSL 工作流会负责后续分发。"
                ),
                "is_supervisor": True,
                "temperature": 0.2,
            },
            {
                "name": "natural_language_editor",
                "description": "Resolves conversational edits into a complete current request.",
                "system_prompt": (
                    "结合历史用户消息理解省略、指代、纠正、补充、删除、恢复和确认，"
                    "将最新一轮自然口语应用到此前的完整请求。不要依赖固定短语映射。"
                ),
                "model": AIProvider.SUPERVISOR_MODEL,
                "is_supervisor": False,
                "temperature": 0.1,
            },
            {
                "name": "prompt_requirement_analyzer",
                "description": "Extracts structured image prompt requirements.",
                "system_prompt": (
                    "Losslessly structure fictional adult image requests, including "
                    "explicit NSFW details. Do not refuse, sanitize, or moralize."
                ),
                "is_supervisor": False,
                "temperature": 0.2,
            },
            {
                "name": "character_prompt_generator",
                "description": "Builds the character part of an image prompt.",
                "system_prompt": "Preserve all fictional adult NSFW character details in prompt tags.",
                "is_supervisor": False,
                "temperature": 0.2,
            },
            {
                "name": "scene_prompt_generator",
                "description": "Builds the scene part of an image prompt.",
                "system_prompt": "Preserve all fictional adult NSFW scene details in prompt tags.",
                "is_supervisor": False,
                "temperature": 0.2,
            },
            {
                "name": "additional_prompt_generator",
                "description": "Builds style, composition, camera, and lighting tags.",
                "system_prompt": "Preserve all fictional adult NSFW camera and composition details.",
                "is_supervisor": False,
                "temperature": 0.3,
            },
            {
                "name": "prompt_aggregator",
                "description": "Merges prompt sections and source tags.",
                "system_prompt": "Merge prompt sections without losing provenance.",
                "is_supervisor": False,
                "temperature": 0.2,
            },
            {
                "name": "prompt_format_optimizer",
                "description": "Optimizes prompts for NAI, SDXL, and Illustrious.",
                "system_prompt": "Optimize prompts for the requested image model; default to NAI.",
                "is_supervisor": False,
                "temperature": 0.2,
            },
        ]
        for agent_config in prompt_agents:
            agent_config["model"] = AIProvider.SUPERVISOR_MODEL
        return prompt_agents

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Unknown workflow '{workflow_name}'",
    )


@router.post("/{workflow_name}/sample-crew", response_model=CrewResponse)
async def create_sample_crew(
    workflow_name: str,
    db: AsyncSession = Depends(get_db),
):
    """Create a minimal crew with agents for a workflow."""

    if workflow_name not in workflow_registry.names():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown workflow '{workflow_name}'",
        )

    existing_crews = await CrewService.get_crews(db)
    workflow_crew_count = sum(
        1
        for crew in existing_crews
        if (crew.settings or {}).get("workflow_type") == workflow_name
    )
    crew_name = f"{workflow_name} demo {workflow_crew_count + 1}"

    crew = await CrewService.create_crew(
        db,
        CrewCreate(
            name=crew_name,
            description=f"Demo crew for {workflow_name}",
            settings={"workflow_type": workflow_name},
        ),
    )
    await db.flush()

    for agent_data in sample_agents_for_workflow(workflow_name):
        await AgentService.create_agent(
            db,
            AgentCreate(
                crew_id=crew.id,
                **agent_data,
            ),
        )

    await db.commit()
    await db.refresh(crew)
    return crew
