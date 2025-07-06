from workflows.workflow import build_healthbot_workflow
from langchain_core.messages import HumanMessage

if __name__ == "__main__":
    workflow = build_healthbot_workflow()

    result = workflow.invoke({
        "user_id": "user_xyz",
        "location": "Indore",  # simulate GPS data
        "messages": [HumanMessage(content="I'm having serious chest pain, what to do?.,suggest instant heart attack , suggest nearby hospital and medicine")],
    })

    print("\n=== Final Response ===\n")
    print(result["response_message"])
