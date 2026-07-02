"""Base protocol for callable tools."""

from typing import Any, Dict, Protocol


class ToolRunner(Protocol):
    """Interface implemented by concrete tool runners."""

    async def run(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Run a tool call and return structured results."""
