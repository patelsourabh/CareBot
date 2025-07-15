from langgraph.graph import StateGraph, END, add_messages
from langchain_tavily import TavilySearch
from shared.types import HealthBotState
from typing import TypedDict, Annotated
from dotenv import load_dotenv
import os
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_community.chat_models import ChatOpenAI

load_dotenv()

llm = ChatOpenAI(
    model="mistralai/mistral-7b-instruct", 
    openai_api_key=os.environ["OPENROUTER_API_KEY"],
    openai_api_base="https://openrouter.ai/api/v1"
)



search_prompt = PromptTemplate.from_template(
    "You are an expert medical assistant. Rewrite this user query to make it ideal for an accurate online search: {query}"
)

query_rewriter = search_prompt | llm | (lambda x: x.content.strip())

search_tool = TavilySearch(k=2, tavily_api_key=os.getenv("TAVILY_API_KEY"))


class InfoState(TypedDict):
    messages: Annotated[list, add_messages]
    location: str
    symptoms: list
    _search_topic: str
    _search_results: list


def search_topic_node(state: HealthBotState) -> HealthBotState:
    user_messages = [m for m in state["messages"] if m.type == "human"]
    user_query = user_messages[-1].content.strip() if user_messages else ""
    user_location = state.get("location", "").strip()

    if not user_query:
        state["_search_topic"] = None
        return state

    try:
        # query with striping
        rewritten = query_rewriter.invoke({"query": user_query})
        rewritten = rewritten.strip().strip('"').strip("'")

        # appends location if not present
        query_lower = rewritten.lower()
        if ("near me" in query_lower or "nearby" in query_lower) and user_location:
            improved_query = f"{rewritten.replace('near me', '').replace('nearby', '')} in {user_location}"
        elif user_location and user_location.lower() not in query_lower:
            improved_query = f"{rewritten}, {user_location}"
        else:
            improved_query = rewritten

        print(f"&& Final query to search: {improved_query}")
        state["_search_topic"] = improved_query
    except Exception as e:
        print(f"&& Query rewriting failed: {e}")
        state["_search_topic"] = user_query

    return state



# tavily search

def search_node(state: HealthBotState) -> HealthBotState:
    topic = state.get("_search_topic")
    print(f"### Entered info_search search_node with topic: {topic}")
    if not topic:
        return state

    try:
        result = search_tool.invoke(topic)
        print("### Tavily raw result:", result)
        
        if isinstance(result, dict) and "results" in result:
            state["_search_results"] = result["results"]
        else:
            state["_search_results"] = [result]  # Fallback 
    except Exception as e:
        state["_search_results"] = [{"title": "Search Error", "content": str(e)}]

    return state




def summarizer_node(state: HealthBotState) -> HealthBotState:
    print("** Entered info_search summarizer_node")
    
    topic = state.get("_search_topic")
    raw = state.get("_search_results")

    outputs = dict(state.get("agent_outputs", {})) 

    if not topic:
        print("** No search topic found")
        outputs["info_search"] = "**No topic provided for information search."
        state["agent_outputs"] = outputs
        return state

    if not raw:
        print("** No search results found")
        outputs["info_search"] = f"** No results found for: '{topic}'."
        state["agent_outputs"] = outputs
        return state

    items = raw.get("results") if isinstance(raw, dict) else raw
    contents = [r["content"].strip() for r in items if "content" in r]

    if not contents:
        print("** Search results are empty or missing content field.")
        outputs["info_search"] = f"** Found search topic '{topic}', but no content to summarize."
        state["agent_outputs"] = outputs
        return state

    combined = "\n\n".join(contents)
    outputs["info_search"] = combined
    state["agent_outputs"] = outputs

    print("** [info_search_agent] stored info_search inn agent_output:", combined[:200])
    return state




#graph

info_graph = StateGraph(HealthBotState)
info_graph.add_node("search_topic_node", search_topic_node)
info_graph.add_node("search_node", search_node)
info_graph.add_node("summarizer_node", summarizer_node)
info_graph.set_entry_point("search_topic_node")
info_graph.add_edge("search_topic_node", "search_node")
info_graph.add_edge("search_node", "summarizer_node")
info_graph.set_finish_point("summarizer_node")

info_search_agent = info_graph.compile()
