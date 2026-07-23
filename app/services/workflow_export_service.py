"""Build database-free standalone packages from registered workflows."""

from __future__ import annotations

import ast
import importlib.metadata
import io
import json
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from app.agents.catalog import resolve_workflow_agent_configs
from app.core.langgraph.workflows.registry import workflow_registry


ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "app"
WORKFLOWS_DIR = APP_DIR / "core" / "langgraph" / "workflows"
EXPORT_ROOT_SUFFIX = "standalone"
FORBIDDEN_MODULE_PREFIXES = (
    "app.api",
    "app.db",
    "app.models",
    "app.schemas",
)
PACKAGE_NAMES = {
    "aiohttp": "aiohttp",
    "dotenv": "python-dotenv",
    "httpx": "httpx",
    "langchain": "langchain",
    "langchain_core": "langchain-core",
    "langchain_openai": "langchain-openai",
    "langgraph": "langgraph",
    "langgraph_supervisor": "langgraph-supervisor",
    "openai": "openai",
    "pydantic": "pydantic",
    "tenacity": "tenacity",
    "typing_extensions": "typing-extensions",
}


@dataclass(frozen=True)
class WorkflowExport:
    """One generated ZIP artifact."""

    filename: str
    content: bytes
    file_count: int


class LocalDependencyCollector:
    """Collect local ``app`` modules reachable through Python imports."""

    def __init__(self) -> None:
        self.files: set[Path] = set()
        self.external_modules: set[str] = set()
        self._processed: set[Path] = set()

    def add_tree(self, directory: Path) -> None:
        for path in sorted(directory.rglob("*")):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            if path.suffix in {".pyc", ".pyo"}:
                continue
            self.files.add(path)
            if path.suffix == ".py":
                self._scan(path)

    def add_module(self, module_name: str) -> None:
        if any(
            module_name == prefix or module_name.startswith(f"{prefix}.")
            for prefix in FORBIDDEN_MODULE_PREFIXES
        ):
            raise ValueError(
                f"Standalone export cannot include platform module '{module_name}'"
            )
        path = self._module_path(module_name)
        if path is None:
            if module_name == "app" or module_name.startswith("app."):
                return
            top_level = module_name.split(".", 1)[0]
            if top_level not in sys.stdlib_module_names and top_level != "__future__":
                self.external_modules.add(top_level)
            return
        self._add_python_file(path)

    def _add_python_file(self, path: Path) -> None:
        if path in self._processed:
            return
        self.files.add(path)
        self._processed.add(path)
        for parent in path.parents:
            if parent == ROOT:
                break
            init_path = parent / "__init__.py"
            if init_path.is_file() and init_path not in self._processed:
                self._add_python_file(init_path)
        self._scan_imports(path)

    def _scan(self, path: Path) -> None:
        if path in self._processed:
            return
        self._processed.add(path)
        self.files.add(path)
        self._scan_imports(path)

    def _scan_imports(self, path: Path) -> None:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError, UnicodeError) as exc:
            raise ValueError(f"Cannot analyze Python source '{path}': {exc}") from exc

        current_module = self._module_name(path)
        current_package = (
            current_module
            if path.name == "__init__.py"
            else current_module.rpartition(".")[0]
        )
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.add_module(alias.name)
            elif isinstance(node, ast.ImportFrom):
                base = self._absolute_import(current_package, node.module, node.level)
                if base:
                    self.add_module(base)
                    for alias in node.names:
                        if alias.name != "*":
                            self.add_module(f"{base}.{alias.name}")

    @staticmethod
    def _absolute_import(package: str, module: str | None, level: int) -> str:
        if level == 0:
            return module or ""
        parts = package.split(".") if package else []
        keep = max(0, len(parts) - level + 1)
        prefix = parts[:keep]
        if module:
            prefix.extend(module.split("."))
        return ".".join(prefix)

    @staticmethod
    def _module_name(path: Path) -> str:
        relative = path.relative_to(ROOT)
        parts = list(relative.with_suffix("").parts)
        if parts[-1] == "__init__":
            parts.pop()
        return ".".join(parts)

    @staticmethod
    def _module_path(module_name: str) -> Path | None:
        if not module_name.startswith("app"):
            return None
        base = ROOT.joinpath(*module_name.split("."))
        module_file = base.with_suffix(".py")
        if module_file.is_file():
            return module_file
        package_file = base / "__init__.py"
        if package_file.is_file():
            return package_file
        return None


def _agent_directories(metadata: dict[str, Any]) -> list[Path]:
    names = {
        str(node.get("agent") or node.get("name") or "").strip()
        for node in metadata.get("nodes") or []
    }
    found: dict[str, Path] = {}
    for manifest_path in APP_DIR.joinpath("agents").rglob("config_defaults.json"):
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        name = str(manifest.get("name") or "").strip()
        if name in names:
            found[name] = manifest_path.parent
    missing = sorted(names - found.keys())
    if missing:
        raise ValueError(f"Missing local Agent packages: {', '.join(missing)}")
    return [found[name] for name in sorted(found)]


def _standalone_config() -> str:
    return '''"""Environment-only settings for the standalone workflow."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    openrouter_base_url: str = os.getenv(
        "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
    )
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    llm_default_model: str = os.getenv("LLM_DEFAULT_MODEL", "gpt-5.4")
    llm_supervisor_model: str = os.getenv("LLM_SUPERVISOR_MODEL", "gpt-5.5")
    llm_request_timeout_seconds: float = float(
        os.getenv("LLM_REQUEST_TIMEOUT_SECONDS", "75")
    )
    short_term_memory_turns: int = int(os.getenv("SHORT_TERM_MEMORY_TURNS", "10"))
    long_term_memory_enabled: bool = False
    long_term_memory_limit: int = 0


settings = Settings()
'''


def _standalone_checkpoint() -> str:
    return '''"""Process-local short-term LangGraph checkpoint."""

from langgraph.checkpoint.memory import MemorySaver


_checkpointer = MemorySaver()


async def init_checkpointer():
    return _checkpointer


async def close_checkpointer() -> None:
    return None


def get_checkpointer():
    return _checkpointer
'''


def _standalone_store() -> str:
    return '''"""Long-term memory is intentionally disabled in standalone exports."""


async def init_store():
    return None


async def close_store() -> None:
    return None


def get_store():
    return None
'''


def _runner_source(
    workflow_name: str,
    factory_module: str,
    factory_name: str,
    state_builder_name: str,
) -> str:
    return f'''"""Public runtime API for the exported workflow."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.types import Command

from {factory_module} import {factory_name}
from app.core.langgraph.workflows.{workflow_name}.state import {state_builder_name}


ROOT = Path(__file__).resolve().parent
AGENT_CONFIGS = json.loads((ROOT / "agent_configs.json").read_text(encoding="utf-8"))
WORKFLOW_METADATA = json.loads((ROOT / "workflow.json").read_text(encoding="utf-8"))


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {{str(key): _json_safe(item) for key, item in value.items()}}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "model_dump"):
        return _json_safe(value.model_dump())
    return str(value)


def extract_output(state: dict[str, Any]) -> Any:
    nodes = state.get("nodes") or {{}}
    for node in reversed(WORKFLOW_METADATA.get("nodes") or []):
        node_state = nodes.get(node.get("name")) or {{}}
        for key in ("final_output", "answer", "formatted_prompt", "results", "output"):
            value = node_state.get(key)
            if value not in (None, "", [], {{}}):
                return _json_safe(value)
    return _json_safe(state)


class WorkflowRuntime:
    """In-process workflow runtime with non-persistent short-term memory."""

    def __init__(self, thread_id: str | None = None) -> None:
        self.thread_id = thread_id or str(uuid4())
        self.graph = {factory_name}(crew_id="standalone", agents=AGENT_CONFIGS)
        self.history = []

    async def ainvoke(
        self,
        user_input: str,
        workflow_inputs: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        user_message = HumanMessage(content=user_input)
        max_messages = 20
        state = {state_builder_name}(
            crew_id="standalone",
            agents=AGENT_CONFIGS,
            user_id="standalone-user",
            conversation_id=self.thread_id,
            messages=[*self.history[-max_messages:], user_message],
            user_input=user_input,
            workflow_inputs=workflow_inputs or {{}},
            request_context={{"request_id": str(uuid4()), "thread_id": self.thread_id}},
        )
        config = {{"configurable": {{"thread_id": self.thread_id}}, "recursion_limit": 100}}
        result = await self.graph.ainvoke(state, config=config)
        while result.get("__interrupt__"):
            interrupt_item = result["__interrupt__"][0]
            payload = getattr(interrupt_item, "value", interrupt_item)
            question = payload.get("question") if isinstance(payload, dict) else str(payload)
            answer = input(f"{{question}}\\n> ").strip()
            result = await self.graph.ainvoke(Command(resume=answer), config=config)
        output = extract_output(result)
        self.history.extend([user_message, AIMessage(content=json.dumps(output, ensure_ascii=False))])
        self.history = self.history[-max_messages:]
        return result
'''


def _main_source() -> str:
    return '''"""Interactive command-line runner."""

import asyncio
import json

from standalone_workflow.runtime import WorkflowRuntime, extract_output


async def main() -> None:
    runtime = WorkflowRuntime()
    print("Standalone LangGraph workflow. Type /exit to quit.")
    while True:
        text = input("You> ").strip()
        if text.lower() in {"/exit", "/quit"}:
            return
        if not text:
            continue
        state = await runtime.ainvoke(text)
        print(json.dumps(extract_output(state), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
'''


def _readme(workflow_name: str) -> str:
    return f"""# {workflow_name} 独立 LangGraph 包

本包由 LangGraph Multi-Agent Workflow Studio 自动导出，只包含工作流、相关 Agent、业务模块和最小运行时。

## 能力边界

- 不包含前端、FastAPI、数据库模型或平台服务。
- 使用 LangGraph `MemorySaver` 保存进程内短期状态。
- 不启用长期记忆；进程退出后短期状态自动清空。
- Agent 配置与 Workflow 元数据已快照到包内，不需要数据库同步。

## 运行

```powershell
python -m venv .venv
.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python -m standalone_workflow
```

请在 `.env` 中填写模型 API Key 和地址。也可以作为 Python 模块调用：

```python
import asyncio
from standalone_workflow import WorkflowRuntime, extract_output

async def main():
    runtime = WorkflowRuntime(thread_id="demo")
    state = await runtime.ainvoke(
        "你的任务",
        workflow_inputs={{"target_model": "nai_v4"}},
    )
    print(extract_output(state))

asyncio.run(main())
```
"""


def _requirements(external_modules: Iterable[str]) -> str:
    packages = {
        PACKAGE_NAMES.get(module, module.replace("_", "-"))
        for module in external_modules
        if module not in sys.stdlib_module_names and module != "__future__"
    }
    packages.update({"langgraph", "langchain-core", "python-dotenv"})
    lines = []
    for package in sorted(packages, key=str.lower):
        try:
            version = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            lines.append(package)
        else:
            lines.append(f"{package}=={version}")
    return "\n".join(lines) + "\n"


def _external_modules_from_sources(sources: Iterable[str]) -> set[str]:
    """Read third-party imports from the final source text written to the ZIP."""

    modules: set[str] = set()
    for source in sources:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module]
            for name in names:
                top_level = name.split(".", 1)[0]
                if (
                    top_level != "app"
                    and top_level != "standalone_workflow"
                    and top_level != "__future__"
                    and top_level not in sys.stdlib_module_names
                ):
                    modules.add(top_level)
    return modules


def export_workflow(workflow_name: str) -> WorkflowExport:
    """Export one registered workflow as a self-contained ZIP archive."""

    if workflow_name not in workflow_registry.names():
        raise KeyError(workflow_name)
    workflow_dir = WORKFLOWS_DIR / workflow_name
    if not workflow_dir.joinpath("graph.py").is_file():
        raise ValueError(f"Workflow source directory '{workflow_dir}' is missing")

    spec = workflow_registry.get_spec(workflow_name, fallback=False)
    metadata = workflow_registry.get_metadata(workflow_name, fallback=False)
    factory_module = spec.factory.__module__
    factory_name = spec.factory.__name__
    if spec.state_builder is None:
        raise ValueError(f"Workflow '{workflow_name}' has no initial-state builder")

    collector = LocalDependencyCollector()
    collector.add_tree(workflow_dir)
    for agent_dir in _agent_directories(metadata):
        collector.add_tree(agent_dir)
    collector.add_module(factory_module)

    agent_configs = resolve_workflow_agent_configs(metadata)
    dsl_path = ROOT / "examples" / "workflows" / f"{workflow_name}.json"
    root_name = f"{workflow_name}-{EXPORT_ROOT_SUFFIX}"
    replacements = {
        Path("app/core/config.py"): _standalone_config(),
        Path("app/core/langgraph/checkpoint.py"): _standalone_checkpoint(),
        Path("app/core/langgraph/store.py"): _standalone_store(),
    }
    generated = {
        Path("standalone_workflow/__init__.py"): (
            "from standalone_workflow.runtime import "
            "WorkflowRuntime, extract_output\n\n"
            "__all__ = [\"WorkflowRuntime\", \"extract_output\"]\n"
        ),
        Path("standalone_workflow/__main__.py"): _main_source(),
        Path("standalone_workflow/runtime.py"): _runner_source(
            workflow_name,
            factory_module,
            factory_name,
            spec.state_builder.__name__,
        ),
        Path("standalone_workflow/agent_configs.json"): json.dumps(
            agent_configs, ensure_ascii=False, indent=2
        ) + "\n",
        Path("standalone_workflow/workflow.json"): json.dumps(
            {"name": workflow_name, **metadata}, ensure_ascii=False, indent=2
        ) + "\n",
        Path("README.md"): _readme(workflow_name),
        Path(".env.example"): (
            "OPENROUTER_API_KEY=\n"
            "OPENROUTER_BASE_URL=https://openrouter.ai/api/v1\n"
            "LLM_DEFAULT_MODEL=gpt-5.4\n"
            "LLM_SUPERVISOR_MODEL=gpt-5.5\n"
            "LLM_REQUEST_TIMEOUT_SECONDS=75\n"
            "SHORT_TERM_MEMORY_TURNS=10\n"
        ),
    }
    if dsl_path.is_file():
        generated[Path("standalone_workflow/workflow.dsl.json")] = (
            dsl_path.read_text(encoding="utf-8")
        )

    final_python_sources = []
    for source in collector.files:
        if source.suffix != ".py":
            continue
        relative = source.relative_to(ROOT)
        final_python_sources.append(
            replacements.get(relative) or source.read_text(encoding="utf-8")
        )
    final_python_sources.extend(
        content for path, content in generated.items() if path.suffix == ".py"
    )
    generated[Path("requirements.txt")] = _requirements(
        _external_modules_from_sources(final_python_sources)
    )

    buffer = io.BytesIO()
    written: set[Path] = set()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for source in sorted(collector.files):
            relative = source.relative_to(ROOT)
            if relative in replacements:
                content = replacements[relative].encode("utf-8")
            else:
                content = source.read_bytes()
            archive.writestr(f"{root_name}/{relative.as_posix()}", content)
            written.add(relative)
        for relative, content in {**replacements, **generated}.items():
            if relative in written:
                continue
            archive.writestr(f"{root_name}/{relative.as_posix()}", content.encode("utf-8"))
            written.add(relative)

    return WorkflowExport(
        filename=f"{root_name}.zip",
        content=buffer.getvalue(),
        file_count=len(written),
    )
