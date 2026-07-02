"""Registry for concrete agent runners."""

from typing import Dict, Optional

from app.agents.base import AgentRunner


class AgentRegistry:
    """Small registry used to look up agent runner implementations."""

    def __init__(self) -> None:
        self._runners: Dict[str, AgentRunner] = {}

    def register(self, name: str, runner: AgentRunner) -> None:
        self._runners[name] = runner

    def get(self, name: str) -> Optional[AgentRunner]:
        return self._runners.get(name)

    def names(self) -> list[str]:
        return sorted(self._runners)


agent_registry = AgentRegistry()
