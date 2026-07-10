"""Business nodes for the baseball_analysis_agent agent.

This example is inspired by aws-samples/langgraph-multi-agent: plan a baseball
analysis task, retrieve function knowledge, generate code, execute it, then
summarize the result. The sample stays deterministic and dependency-free so it
can run in this template's test suite.
"""

from typing import Any, Dict

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig

from app.agents.baseball_analysis_agent.state import BaseballAnalysisAgentState

# 本文件由 scripts/generate_agent.py 刷新骨架。
# 中文注意：
# - 只在 <agent-node ...> 代码块内部编写业务逻辑。
# - 节点名是 DSL 的稳定标识；节点名不变，刷新时保留对应代码块。
# - 新 DSL 删除某个节点名时，对应代码块会被删除，即使里面有人写过业务代码。


def _user_question(state: BaseballAnalysisAgentState) -> str:
    return str(state.get("user_input") or "").strip()


# <agent-node name="plan">
# 中文注意：
# 1. 节点名 "plan" 是 DSL 的稳定标识，不要随手改名。
# 2. 只要 DSL 里还保留这个节点名，刷新骨架时会保留本代码块里的业务逻辑。
# 3. 如果新 DSL 删除了这个节点名，生成器会删除整个代码块，即使里面写过业务代码。
def plan_node(
    state: BaseballAnalysisAgentState,
    config: RunnableConfig | None = None,
) -> Dict[str, Any]:
    """Create a small analysis plan from the user question."""

    question = _user_question(state)
    task = question or "Answer a baseball statistics question."
    plan = (
        "1. Identify the requested baseball statistic.\n"
        "2. Retrieve the relevant data function or known example.\n"
        "3. Draft Python-style analysis code.\n"
        "4. Execute the safe built-in example.\n"
        "5. Summarize the numeric result."
    )
    return {
        "task": task,
        "plan": plan,
    }
# </agent-node>


# <agent-node name="retrieve">
# 中文注意：
# 1. 节点名 "retrieve" 是 DSL 的稳定标识，不要随手改名。
# 2. 只要 DSL 里还保留这个节点名，刷新骨架时会保留本代码块里的业务逻辑。
# 3. 如果新 DSL 删除了这个节点名，生成器会删除整个代码块，即使里面写过业务代码。
def retrieve_node(
    state: BaseballAnalysisAgentState,
    config: RunnableConfig | None = None,
) -> Dict[str, Any]:
    """Retrieve a lightweight function hint for the planned task."""

    task = str(state.get("task") or "").lower()
    if "jeter" in task and ("home run" in task or "homer" in task):
        detail = (
            "Use batting_stats_range(start_dt, end_dt) and filter player_name "
            "for Derek Jeter, then read the HR column."
        )
    else:
        detail = (
            "Use a baseball statistics lookup, filter to the requested player "
            "or team, then aggregate the requested stat."
        )
    return {"function_detail": detail}
# </agent-node>


# <agent-node name="generate_code">
# 中文注意：
# 1. 节点名 "generate_code" 是 DSL 的稳定标识，不要随手改名。
# 2. 只要 DSL 里还保留这个节点名，刷新骨架时会保留本代码块里的业务逻辑。
# 3. 如果新 DSL 删除了这个节点名，生成器会删除整个代码块，即使里面写过业务代码。
def generate_code_node(
    state: BaseballAnalysisAgentState,
    config: RunnableConfig | None = None,
) -> Dict[str, Any]:
    """Draft code matching the retrieved function detail."""

    code = (
        "from pybaseball import batting_stats_range\n"
        "data = batting_stats_range('2010-01-01', '2010-12-31')\n"
        "jeter = data[data['Name'].str.contains('Derek Jeter', case=False)]\n"
        "answer = int(jeter['HR'].sum())"
    )
    return {"code": code}
# </agent-node>


# <agent-node name="execute_code">
# 中文注意：
# 1. 节点名 "execute_code" 是 DSL 的稳定标识，不要随手改名。
# 2. 只要 DSL 里还保留这个节点名，刷新骨架时会保留本代码块里的业务逻辑。
# 3. 如果新 DSL 删除了这个节点名，生成器会删除整个代码块，即使里面写过业务代码。
def execute_code_node(
    state: BaseballAnalysisAgentState,
    config: RunnableConfig | None = None,
) -> Dict[str, Any]:
    """Execute a safe built-in example result instead of arbitrary code."""

    task = str(state.get("task") or "").lower()
    if "jeter" in task and "2010" in task and ("home run" in task or "homer" in task):
        result = {
            "stat": "home_runs",
            "player": "Derek Jeter",
            "season": 2010,
            "value": 10,
            "source": "built-in example adapted from the AWS LangGraph sample",
        }
    else:
        result = {
            "stat": "unknown",
            "value": None,
            "source": "built-in fallback",
            "error": "No built-in baseball example matched this request.",
        }
    return {"execution_result": result}
# </agent-node>


# <agent-node name="summarize">
# 中文注意：
# 1. 节点名 "summarize" 是 DSL 的稳定标识，不要随手改名。
# 2. 只要 DSL 里还保留这个节点名，刷新骨架时会保留本代码块里的业务逻辑。
# 3. 如果新 DSL 删除了这个节点名，生成器会删除整个代码块，即使里面写过业务代码。
def summarize_node(
    state: BaseballAnalysisAgentState,
    config: RunnableConfig | None = None,
) -> Dict[str, Any]:
    """Summarize the execution result for the caller."""

    result = state.get("execution_result") or {}
    if result.get("value") is None:
        answer = (
            "I could not match this request to the built-in baseball analysis "
            "example yet. The generated plan and code skeleton are available "
            "for extension."
        )
    else:
        answer = (
            f"{result['player']} hit {result['value']} home runs in "
            f"{result['season']}."
        )

    messages = list(state.get("messages") or [])
    messages.append(AIMessage(content=answer, name="baseball_analysis_agent"))
    return {
        "answer": answer,
        "messages": messages,
    }
# </agent-node>
