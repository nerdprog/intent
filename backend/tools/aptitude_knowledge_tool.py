"""retrieve_aptitude_knowledge — MCP-ready knowledge tool."""

from typing import List, Optional

from backend.rag.retrieval import retrieve_aptitude_knowledge, retrieve_as_text


def retrieve_aptitude_knowledge_tool(
    topic: str,
    query: str = "",
    section: Optional[str] = None,
    k: int = 3,
) -> List[dict]:
    return retrieve_aptitude_knowledge(topic=topic, query=query, section=section, k=k)


def get_topic_lesson_text(topic: str, query: str = "", mastery: int = 40) -> str:
    return retrieve_as_text(topic=topic, query=query, mastery=mastery)
