from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage
from shared.types import HealthBotState
from typing import TypedDict, Annotated
from langgraph.graph import add_messages
from dotenv import load_dotenv
import os

load_dotenv()

# LLM
llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
search_tool = TavilySearchResults(max_results=1)

class InfoState(TypedDict):
    messages: Annotated[list, add_messages]
    response_message: str
    location: str
    symptoms: list
    _search_topic: str
    _search_results: list
    _info_mode: str  # "medicine", "hospital", or None

# ==== Node: LLM decides if search needed and what to search ====

def llm_node(state: HealthBotState) -> HealthBotState:
    user_query = state["messages"][-1].content.lower()

    hospital_keywords = ["hospital", "clinic", "doctor", "emergency", "medical care", "emergency medical care"]
    medicine_keywords = ["medicine", "painkiller", "drug", "dosage", "heart attack medicine", "aspirin"]

    location = state.get('location', 'your city')

    # Check for medicine explicitly first
    if any(k in user_query for k in medicine_keywords):
        state["_info_mode"] = "medicine"
        state["_search_topic"] = "medicine for heart attack"  # hardcoded override for clarity
        return state

    if any(k in user_query for k in hospital_keywords):
        state["_info_mode"] = "hospital"
        state["_search_topic"] = f"Best hospitals in {location}"
        return state

    state["_info_mode"] = None
    state["_search_topic"] = None
    return state


# ==== Node: Do search manually ====

def search_node(state: HealthBotState) -> HealthBotState:
    topic = state.get("_search_topic")
    if not topic:
        return state

    try:
        result = search_tool.invoke(topic)
        state["_search_results"] = result
    except Exception as e:
        state["_search_results"] = [{"title": "Search Error", "url": str(e)}]

    return state

# ==== Node: Summarize results ====

def summarizer_node(state: HealthBotState) -> HealthBotState:
    topic = state.get("_search_topic")
    results = state.get("_search_results", [])
    mode = state.get("_info_mode")

    if not topic or not results:
        return state

    urls_content = "\n".join([f"{r['title']}: {r['url']}" for r in results])

    prompt = f"""You are a health assistant. Summarize this info for the query: '{topic}'.
    Summarize useful parts only, no links or ads. Here's the source content:\n\n{urls_content}"""

    result = llm.invoke([HumanMessage(content=prompt)])

    if mode == "medicine":
        state["response_message"] += f"\n\n💊 Medicine Info:\n{result.content}\n⚠️ Only use medicines after consulting a doctor."
    elif mode == "hospital":
        state["response_message"] += f"\n\n🏥 Hospital Info:\n{result.content}\n⚠️ Visit hospitals only after checking with a doctor."

    return state

# ==== Graph ====

info_graph = StateGraph(HealthBotState)

info_graph.add_node("llm_node", llm_node)
info_graph.add_node("search_node", search_node)
info_graph.add_node("summarizer_node", summarizer_node)

info_graph.set_entry_point("llm_node")
info_graph.add_edge("llm_node", "search_node")
info_graph.add_edge("search_node", "summarizer_node")
info_graph.set_finish_point("summarizer_node")

info_search_agent = info_graph.compile()
