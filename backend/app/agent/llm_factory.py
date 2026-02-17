"""LLM factory: Ollama (qwen2.5), GigaChat, OpenAI-compatible (cheap/free)."""
from typing import Optional

from langchain_core.language_models import BaseChatModel

from app.config import settings
from app.db.models import LLMType


def get_llm(
    llm_type: str,
    model: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> BaseChatModel:
    """
    Return LangChain chat model for agent.
    llm_type: ollama | gigachat | openai
    """
    if llm_type == LLMType.ollama.value:
        from langchain_community.chat_models import ChatOllama
        # num_ctx: контекст по умолчанию 4096 — промпт 18k+ обрезается. Qwen2.5 поддерживает 32k.
        return ChatOllama(
            model=model or "qwen2.5:7b",
            base_url=base_url or "http://localhost:11434",
            temperature=0.2,
            num_ctx=settings.ollama_num_ctx,
        )
    if llm_type == LLMType.gigachat.value:
        try:
            from langchain_community.chat_models import GigaChat
        except ImportError:
            raise ImportError("GigaChat: pip install langchain-community (and gigachat if needed)")
        return GigaChat(
            credentials=api_key,
            model=model or "GigaChat",
            verify_ssl_certs=False,
            temperature=0.2,
        )
    if llm_type == LLMType.openai.value:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model or "gpt-4o-mini",
            api_key=api_key,
            base_url=base_url,
            temperature=0.2,
        )
    raise ValueError(f"Unknown llm_type: {llm_type}")
