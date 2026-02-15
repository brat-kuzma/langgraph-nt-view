"""LangGraph graph: collect -> analyze -> format report."""
from typing import Any, Optional

from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from app.agent.state import AgentState
from app.agent.nodes import analyze_artifacts, format_report_text
from app.agent.llm_factory import get_llm
from app.config import settings


def create_agent_graph(
    llm_type: str = "ollama",
    llm_model: str = "qwen2.5vl:7b",
    llm_api_key: Optional[str] = None,
    llm_base_url: Optional[str] = None,
):
    """Build compiled graph with given LLM."""
    llm = get_llm(llm_type, llm_model, api_key=llm_api_key, base_url=llm_base_url or getattr(settings, "ollama_base_url", None))

    workflow = StateGraph(AgentState)

    def analyze_node(state: AgentState) -> AgentState:
        return analyze_artifacts(state, llm)

    workflow.add_node("analyze", analyze_node)
    workflow.add_node("format", format_report_text)

    workflow.add_edge(START, "analyze")
    workflow.add_edge("analyze", "format")
    workflow.add_edge("format", END)

    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)


def run_analysis(
    test_meta: dict,
    artifact_contents: str,
    system_prompt: Optional[str] = None,
    llm_type: str = "ollama",
    llm_model: str = "qwen2.5vl:7b",
    llm_api_key: Optional[str] = None,
    llm_base_url: Optional[str] = None,
) -> dict:
    """
    Run agent and return final state with report_text and report_sections.
    """
    graph = create_agent_graph(
        llm_type=llm_type,
        llm_model=llm_model,
        llm_api_key=llm_api_key,
        llm_base_url=llm_base_url,
    )
    initial: AgentState = {
        "test_meta": test_meta,
        "artifact_contents": artifact_contents,
        "system_prompt": system_prompt,
    }
    config = {"configurable": {"thread_id": "run_once"}}
    final = None
    for chunk in graph.stream(initial, config):
        for v in chunk.values():
            final = v
    if final and final.get("error"):
        return {"error": final["error"], "report_text": "", "report_sections": {}}
    return {
        "report_text": (final or {}).get("report_text", ""),
        "report_sections": (final or {}).get("report_sections", {}),
        "error": (final or {}).get("error"),
    }
