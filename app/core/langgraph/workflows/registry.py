"""Registry for available LangGraph workflows."""

import logging
from typing import Callable, Dict, Optional

from app.core.langgraph.common.errors import WorkflowNotFoundError

logger = logging.getLogger(__name__)

WorkflowFactory = Callable[..., object]


class WorkflowRegistry:
    """Small in-process registry for workflow factories."""

    def __init__(self, default_name: str = "supervisor_simple") -> None:
        self.default_name = default_name
        self._factories: Dict[str, WorkflowFactory] = {}

    def register(self, name: str, factory: WorkflowFactory) -> None:
        self._factories[name] = factory

    def get(self, name: Optional[str] = None, *, fallback: bool = True) -> WorkflowFactory:
        workflow_name = name or self.default_name
        factory = self._factories.get(workflow_name)
        if factory is not None:
            return factory

        if fallback:
            logger.warning(
                "Unsupported workflow_type '%s'; falling back to '%s'",
                workflow_name,
                self.default_name,
            )
            default_factory = self._factories.get(self.default_name)
            if default_factory is not None:
                return default_factory

        raise WorkflowNotFoundError(f"Workflow '{workflow_name}' is not registered")

    def names(self) -> list[str]:
        return sorted(self._factories)


workflow_registry = WorkflowRegistry()
