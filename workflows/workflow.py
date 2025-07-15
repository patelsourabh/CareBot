from langgraph.graph import StateGraph, END
from shared.types import HealthBotState
from typing import List

from agents.symptom_agent import symptom_extractor_agent
from db.postgres_adapter import db_handler_node
from agents.home_remedy_agent import home_remedy_agent
from agents.physical_relief_agent import physical_relief_agent
from agents.info_search_agent import info_search_agent
from agents.intent_classifier_agent import intent_classifier_agent
from agents.general_medical_agent import general_medical_agent
from agents.final_summary_agent import final_summary_agent
from agents.memory_reader_agent import memory_reader_agent
from agents.memory_writer_agent import memory_writer_agent
from agents.emergency_alert_agent import emergency_alert_agent


# Init state 
def init_outputs(state: HealthBotState) -> HealthBotState:
    state.setdefault("agent_outputs", {})
    return state


# Intent routing logic
def route_from_intent(state: HealthBotState) -> List[str]:

    intents = state.get("intents", [])
    print("# Routing based on intents:", intents)

    matched = []
    for intent in intents:
        intent = intent.strip().lower()
        if intent in ["home_remedy", "physical_relief", "info_search", "general_medical"]:
            print(f"# Matched intent: {intent}")
            matched.append(intent)

    if not matched:
        print("# No valid intent matched. Defaulting to memory_reader.")
        return ["memory_reader"]
    
    return matched








# workflow graph
def build_healthbot_workflow():
    graph = StateGraph(HealthBotState)

    # All nodes
    graph.add_node("init_outputs", init_outputs)
    graph.add_node("extract_symptoms", symptom_extractor_agent)
    graph.add_node("emergency_alert", emergency_alert_agent)
    graph.add_node("handle_db", db_handler_node)
    graph.add_node("intent_classifier", intent_classifier_agent)

    graph.add_node("home_remedy", home_remedy_agent)
    graph.add_node("physical_relief", physical_relief_agent)
    graph.add_node("info_search", info_search_agent)
    graph.add_node("general_medical", general_medical_agent)

    graph.add_node("memory_reader", memory_reader_agent)
    graph.add_node("final_summary", final_summary_agent)
    graph.add_node("memory_writer", memory_writer_agent)

    # workflow
    graph.set_entry_point("init_outputs")
    graph.add_edge("init_outputs", "extract_symptoms")
    graph.add_edge("extract_symptoms", "emergency_alert")
    graph.add_edge("emergency_alert", "handle_db")
    graph.add_edge("handle_db", "intent_classifier")

    # Conditional branching 
    graph.add_conditional_edges(
        "intent_classifier",
        route_from_intent,
        {
            "home_remedy": "home_remedy",
            "physical_relief": "physical_relief",
            "info_search": "info_search",
            "general_medical": "general_medical",
            "memory_reader": "memory_reader", 
        }
    )

    
    graph.add_edge("home_remedy", "memory_reader")
    graph.add_edge("physical_relief", "memory_reader")
    graph.add_edge("info_search", "memory_reader")
    graph.add_edge("general_medical", "memory_reader")

    # Final summary + store to memory
    graph.add_edge("memory_reader", "final_summary")
    graph.add_edge("final_summary", "memory_writer")
    graph.add_edge("memory_writer", END)

    print("# Graph ready to compile")

    compiled = graph.compile()
    return compiled
