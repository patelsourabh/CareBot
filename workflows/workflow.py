from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
from shared.types import HealthBotState
from agents.symptom_agent import symptom_extractor_agent
from agents.sqlite_db import db_handler_node
from agents.supervisor_agent import supervisor_node


def build_healthbot_workflow():
    graph = StateGraph(HealthBotState)

    graph.add_node("extract_symptoms", symptom_extractor_agent)
    graph.add_node("handle_db", db_handler_node)
    graph.add_node("supervisor", supervisor_node)

    graph.set_entry_point("extract_symptoms")
    graph.add_edge("extract_symptoms", "handle_db")
    graph.add_edge("handle_db", "supervisor")
    graph.add_edge("supervisor", END)

    return graph.compile()
