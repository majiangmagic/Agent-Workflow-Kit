"""Registry for concrete tool runners."""

from typing import Dict, Optional

from app.tools.base import ToolRunner


class ToolRegistry:
    """Small registry used to look up tool runner implementations."""

    def __init__(self) -> None:
        self._runners: Dict[str, ToolRunner] = {}

    def register(self, name: str, runner: ToolRunner) -> None:
        self._runners[name] = runner

    def get(self, name: str) -> Optional[ToolRunner]:
        return self._runners.get(name)

    def names(self) -> list[str]:
        return sorted(self._runners)


tool_registry = ToolRegistry()
