from db.postgres_adapter import store_conversation

def memory_writer_agent(state: dict) -> dict:
    user_id = state.get("user_id", "unknown_user")

    entry = {
        "user_id": user_id,
        "inputs": state.get("inputs", {}),                
        "results": state.get("agent_outputs", {}),
        "intents": state.get("intents", []),
    }

    try:
        store_conversation(entry)
    except Exception as e:
        print(f"[Memory Write Error] {e}")

    return state
