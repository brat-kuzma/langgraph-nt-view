"""LangGraph agent state for NT report generation."""
from typing import TypedDict, Optional, Any


class AgentState(TypedDict, total=False):
    """State passed between graph nodes."""

    # Input
    test_meta: dict
    artifact_contents: str
    artifact_labels: Optional[list]
    system_prompt: Optional[str]
    max_artifact_chars: Optional[int]  # лимит символов контекста (для Ollama меньше)

    # After analysis
    analysis: str
    report_sections: dict
    report_text: str

    # Errors
    error: Optional[str]
