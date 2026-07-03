"""Base protocol for executable agents."""

from typing import Any, Dict, List, Literal, Optional, Protocol, TypedDict

from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """Runtime state shape for an agent participating in a workflow."""

    agent_id: str
    agent_name: str
    messages: List[BaseMessage]
    status: Literal["idle", "working", "complete", "error"]
    results: Optional[Dict[str, Any]]
    tools: List[Dict[str, Any]]


class AgentRunner(Protocol):
    """Interface implemented by concrete agent runners."""

    async def run(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run an agent task and return structured results."""
