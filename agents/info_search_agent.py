from langgraph.graph import StateGraph, END, add_messages
from langchain_tavily import TavilySearch
from shared.types import HealthBotState
from typing import TypedDict, Annotated
from dotenv import load_dotenv
import os

load_dotenv()

search_tool = TavilySearch(k=3)

class InfoState(TypedDict):
    messages: Annotated[list, add_messages]
    location: str
    symptoms: list
    _search_topic: str
    _search_results: list

# ==== Node: Extract user query for search ====

def search_topic_node(state: HealthBotState) -> HealthBotState:
    user_messages = [m for m in state["messages"] if m.type == "human"]
    user_query = user_messages[-1].content if user_messages else ""

    state["_search_topic"] = user_query.strip() or None
    return state

# ==== Node: Tavily Search ====

def search_node(state: HealthBotState) -> HealthBotState:
    topic = state.get("_search_topic")
    if not topic:
        return state

    try:
        result = search_tool.invoke(topic)
        # ✅ Extract results as list
        if isinstance(result, dict) and "results" in result:
            state["_search_results"] = result["results"]
        else:
            state["_search_results"] = [result]  # Fallback as single item list
    except Exception as e:
        state["_search_results"] = [{"title": "Search Error", "content": str(e)}]

    return state


# ==== Node: Pass content to summarizer agent ====

def summarizer_node(state: HealthBotState) -> HealthBotState:
    print("🚀 Entered info_search summarizer_node")
    
    topic = state.get("_search_topic")
    raw = state.get("_search_results")

    outputs = dict(state.get("agent_outputs", {}))  # ✅ Safe copy

    if not topic:
        print("⚠️ No search topic found")
        outputs["info_search"] = "⚠️ No topic provided for information search."
        state["agent_outputs"] = outputs
        return state

    if not raw:
        print("⚠️ No search results found")
        outputs["info_search"] = f"⚠️ No results found for: '{topic}'."
        state["agent_outputs"] = outputs
        return state

    items = raw.get("results") if isinstance(raw, dict) else raw
    contents = [r["content"].strip() for r in items if "content" in r]

    if not contents:
        print("⚠️ Search results are empty or missing content field.")
        outputs["info_search"] = f"⚠️ Found search topic '{topic}', but no content to summarize."
        state["agent_outputs"] = outputs
        return state

    combined = "\n\n".join(contents)
    outputs["info_search"] = combined
    state["agent_outputs"] = outputs

    print("✅ [info_search_agent] stored info_search:", combined[:200])
    return state




# ==== Graph ====

info_graph = StateGraph(HealthBotState)
info_graph.add_node("search_topic_node", search_topic_node)
info_graph.add_node("search_node", search_node)
info_graph.add_node("summarizer_node", summarizer_node)
info_graph.set_entry_point("search_topic_node")
info_graph.add_edge("search_topic_node", "search_node")
info_graph.add_edge("search_node", "summarizer_node")
info_graph.set_finish_point("summarizer_node")

info_search_agent = info_graph.compile()
