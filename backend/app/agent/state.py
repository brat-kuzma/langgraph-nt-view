"""LangGraph agent state for NT report generation."""
from typing import TypedDict, Optional, Any


class AgentState(TypedDict, total=False):
    """State passed between graph nodes."""

    # Input
    test_meta: dict
    artifact_contents: str
    system_prompt: Optional[str]

    # After analysis
    analysis: str
    report_sections: dict
    report_text: str

    # Errors
    error: Optional[str]
