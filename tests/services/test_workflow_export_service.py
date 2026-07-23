"""Tests for database-free standalone workflow exports."""

import io
import json
import zipfile

import pytest

from app.services import workflow_service as _workflow_service  # noqa: F401
from app.services.workflow_export_service import export_workflow


@pytest.mark.parametrize(
    ("workflow_name", "expected_agent_path"),
    [
        ("supervisor_simple", "app/agents/official_supervisor/workflow_graph.py"),
        (
            "prompt_generation_workflow",
            "app/agents/prompt_generation/prompt_target_renderer/nodes.py",
        ),
    ],
)
def test_export_contains_only_standalone_runtime(
    workflow_name: str,
    expected_agent_path: str,
):
    artifact = export_workflow(workflow_name)
    root = f"{workflow_name}-standalone/"

    with zipfile.ZipFile(io.BytesIO(artifact.content)) as archive:
        names = set(archive.namelist())
        assert f"{root}{expected_agent_path}" in names
        assert f"{root}standalone_workflow/runtime.py" in names
        assert f"{root}standalone_workflow/agent_configs.json" in names
        assert not any(f"{root}app/api/" in name for name in names)
        assert not any(f"{root}app/db/" in name for name in names)
        assert not any(f"{root}app/models/" in name for name in names)
        assert not any(f"{root}frontend/" in name for name in names)

        checkpoint = archive.read(
            f"{root}app/core/langgraph/checkpoint.py"
        ).decode("utf-8")
        store = archive.read(f"{root}app/core/langgraph/store.py").decode("utf-8")
        requirements = archive.read(f"{root}requirements.txt").decode("utf-8")
        configs = json.loads(
            archive.read(f"{root}standalone_workflow/agent_configs.json")
        )

        assert "MemorySaver" in checkpoint
        assert "Postgres" not in checkpoint
        assert "return None" in store
        assert "fastapi" not in requirements.lower()
        assert "sqlalchemy" not in requirements.lower()
        assert configs

        for name in names:
            if name.endswith(".py"):
                compile(archive.read(name), name, "exec")


def test_export_rejects_unknown_workflow():
    with pytest.raises(KeyError):
        export_workflow("missing_workflow")
