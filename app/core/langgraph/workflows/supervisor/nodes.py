"""Node implementations for the supervisor workflow."""

import json
from typing import Any, Dict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.core.langgraph.workflows.supervisor.prompts import (
    AGENT_TASK_PROMPT_TEMPLATE,
    ANALYZE_INPUT_PROMPT,
    COMBINE_RESULTS_PROMPT,
    DIRECT_ANSWER_PROMPT,
    PLAN_PROMPT_TEMPLATE,
)
from app.core.langgraph.workflows.supervisor.state import SupervisorAction, SupervisorState
from app.services.ai_provider import ai_provider


def _model(model_name: str):
    return ai_provider.get_model(model_name)


def analyze_input(state: SupervisorState) -> Dict[str, Any]:
    """Decide whether the supervisor can answer directly or needs a plan."""

    user_input = state["user_input"]
    if not user_input:
        return state

    response = _model("gpt-4-turbo").invoke(
        [
            SystemMessage(content=ANALYZE_INPUT_PROMPT),
            HumanMessage(content=user_input),
        ]
    )

    action = SupervisorAction.CREATE_PLAN
    if "ACTION: ANSWER_DIRECTLY" in response.content.upper():
        action = SupervisorAction.ANSWER_DIRECTLY

    return {
        **state,
        "messages": state["messages"] + [HumanMessage(content=user_input)],
        "action": action,
    }


def answer_directly(state: SupervisorState) -> Dict[str, Any]:
    """Generate a direct response without delegating to other agents."""

    response = _model("gpt-4-turbo").invoke(
        [SystemMessage(content=DIRECT_ANSWER_PROMPT), *state["messages"]]
    )

    return {
        **state,
        "messages": state["messages"] + [response],
        "action": None,
    }


def create_plan(state: SupervisorState) -> Dict[str, Any]:
    """Create a JSON execution plan for the available agents."""

    agent_names = [agent["agent_name"] for agent in state["agents"].values()]
    prompt = PLAN_PROMPT_TEMPLATE.format(agent_names=", ".join(agent_names))
    response = _model("gpt-4-turbo").invoke(
        [
            SystemMessage(content=prompt),
            HumanMessage(content=state["user_input"] or ""),
        ]
    )

    try:
        content = response.content
        if "```json" in content and "```" in content.split("```json", 1)[1]:
            json_str = content.split("```json", 1)[1].split("```", 1)[0]
        elif "```" in content and "```" in content.split("```", 1)[1]:
            json_str = content.split("```", 1)[1].split("```", 1)[0]
        else:
            json_str = content

        plan = json.loads(json_str)
        plan_message = f"Plan created with {len(plan['steps'])} steps to achieve: {plan['goal']}"

        return {
            **state,
            "messages": state["messages"] + [AIMessage(content=plan_message)],
            "plan": plan,
            "action": SupervisorAction.ASSIGN_TASKS,
        }
    except (json.JSONDecodeError, KeyError) as exc:
        return {
            **state,
            "messages": state["messages"]
            + [AIMessage(content=f"Failed to create a valid plan: {str(exc)}")],
            "action": SupervisorAction.ANSWER_DIRECTLY,
        }


def assign_tasks(state: SupervisorState) -> Dict[str, Any]:
    """Assign the next pending plan step to an idle agent."""

    plan = state["plan"]
    if not plan or not plan.get("steps"):
        return state

    updated_agents = {**state["agents"]}
    agent_name_to_id = {
        agent["agent_name"]: agent_id for agent_id, agent in state["agents"].items()
    }

    next_step = None
    for step in plan["steps"]:
        agent_id = agent_name_to_id.get(step["agent"])
        if agent_id and state["agents"][agent_id]["status"] == "idle":
            next_step = step
            break

    if not next_step:
        all_complete = all(
            agent["status"] == "complete"
            for agent in updated_agents.values()
            if any(step["agent"] == agent["agent_name"] for step in plan["steps"])
        )
        return {
            **state,
            "agents": updated_agents,
            "action": SupervisorAction.COMBINE_RESULTS
            if all_complete
            else SupervisorAction.CHECK_STATUS,
        }

    agent_name = next_step["agent"]
    task = next_step["task"]
    agent_id = agent_name_to_id[agent_name]
    updated_agents[agent_id] = {
        **updated_agents[agent_id],
        "status": "working",
        "messages": updated_agents[agent_id]["messages"] + [HumanMessage(content=task)],
    }

    return {
        **state,
        "messages": state["messages"] + [AIMessage(content=f"Assigned task to {agent_name}: {task}")],
        "agents": updated_agents,
        "action": SupervisorAction.CHECK_STATUS,
    }


def check_status(state: SupervisorState) -> Dict[str, Any]:
    """Process working agents and update their results."""

    working_agents = {
        agent_id: agent
        for agent_id, agent in state["agents"].items()
        if agent["status"] == "working"
    }
    if not working_agents:
        return {**state, "action": SupervisorAction.ASSIGN_TASKS}

    updated_agents = {**state["agents"]}
    status_messages = []

    for agent_id, agent in working_agents.items():
        task = next(
            (
                msg.content
                for msg in reversed(agent["messages"])
                if isinstance(msg, HumanMessage)
            ),
            None,
        )
        if not task:
            continue

        try:
            response = _model("gpt-3.5-turbo").invoke(
                [
                    SystemMessage(
                        content=AGENT_TASK_PROMPT_TEMPLATE.format(
                            agent_name=agent["agent_name"]
                        )
                    ),
                    *agent["messages"][-5:],
                ]
            )
            updated_agents[agent_id] = {
                **updated_agents[agent_id],
                "status": "complete",
                "messages": updated_agents[agent_id]["messages"] + [response],
                "results": {"task": task, "response": response.content},
            }
            status_messages.append(f"{agent['agent_name']} completed task: {task[:30]}...")
        except Exception as exc:
            updated_agents[agent_id] = {
                **updated_agents[agent_id],
                "status": "error",
                "messages": updated_agents[agent_id]["messages"]
                + [AIMessage(content=f"Error: {str(exc)}")],
            }
            status_messages.append(f"{agent['agent_name']} encountered an error: {str(exc)}")

    return {
        **state,
        "messages": state["messages"] + [AIMessage(content="\n".join(status_messages))],
        "agents": updated_agents,
        "action": SupervisorAction.ASSIGN_TASKS,
    }


def combine_results(state: SupervisorState) -> Dict[str, Any]:
    """Combine all agent results into a final response."""

    results = []
    for agent in state["agents"].values():
        if agent["results"]:
            results.append(f"Agent {agent['agent_name']}:\n{agent['results']['response']}\n")

    prompt = f"""Original user request: {state["user_input"]}

Plan goal: {state["plan"]["goal"] if state["plan"] and "goal" in state["plan"] else "No specific goal"}

Agent results:
{''.join(results)}

Based on these results, provide a comprehensive response to the user's original request."""

    try:
        response = _model("gpt-4-turbo").invoke(
            [
                SystemMessage(content=COMBINE_RESULTS_PROMPT),
                HumanMessage(content=prompt),
            ]
        )
        return {
            **state,
            "messages": state["messages"] + [response],
            "action": None,
        }
    except Exception as exc:
        return {
            **state,
            "messages": state["messages"]
            + [AIMessage(content=f"Error combining results: {str(exc)}")],
            "action": None,
        }
