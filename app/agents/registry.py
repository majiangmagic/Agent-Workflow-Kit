"""Registry for agent graph factories."""

from typing import Any, Callable, Dict, Optional

AgentGraphFactory = Callable[..., Any]


class AgentRegistry:
    """Small registry used to look up agent graph factories."""

    def __init__(self) -> None:
        self.factories: Dict[str, AgentGraphFactory] = {}

    def register(self, name: str, factory: AgentGraphFactory) -> None:
        self.factories[name] = factory

    def get(self, name: str) -> Optional[AgentGraphFactory]:
        return self.factories.get(name)

    def names(self) -> list[str]:
        return sorted(self.factories)


agent_registry = AgentRegistry()
