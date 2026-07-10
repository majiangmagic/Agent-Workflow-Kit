"""Tests for the generated baseball analysis example agent."""

from langchain_core.messages import AIMessage

from app.agents.baseball_analysis_agent.graph import create_graph
from app.api.routes.conversation import extract_workflow_response


def test_baseball_analysis_agent_runs_sample_question():
    """The generated sample agent should run a deterministic analysis pipeline."""

    graph = create_graph()
    result = graph.invoke(
        {
            "agent_id": "baseball-agent-1",
            "agent_name": "Baseball Analyst",
            "description": "Analyzes baseball statistics.",
            "system_prompt": "Analyze baseball questions.",
            "model": "test-model",
            "temperature": 0.2,
            "tools": [],
            "messages": [],
            "user_input": "How many home runs did Derek Jeter hit in 2010?",
            "plan": None,
            "task": None,
            "function_detail": None,
            "code": None,
            "execution_result": None,
            "answer": None,
        }
    )

    assert result["execution_result"]["value"] == 10
    assert result["answer"] == "Derek Jeter hit 10 home runs in 2010."
    assert isinstance(result["messages"][-1], AIMessage)


def test_extract_workflow_response_falls_back_to_later_agent_answer():
    """Workflow API extraction should prefer later non-supervisor output."""

    final_state = {
        "nodes": {
            "supervisor": {"messages": [AIMessage(content="Intermediate plan")]},
            "baseball_analyst": {
                "answer": "Derek Jeter hit 10 home runs in 2010.",
                "messages": [],
            },
        }
    }

    assert (
        extract_workflow_response(final_state)
        == "Derek Jeter hit 10 home runs in 2010."
    )
