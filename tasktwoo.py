from dotenv import load_dotenv
import os
import json
from typing_extensions import TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END

# loading .env
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise SystemExit("ERROR: GOOGLE_API_KEY not found in .env")

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=api_key)

#class
class CateringState(TypedDict):
    event_date: str
    headcount: int
    menu: list
    capacity_ok: bool
    ingredients_ok: bool
    quote: dict
    status: str
    reason: str

# defining tools
@tool
def capture_request(event_date: str, headcount: int, menu: list):
    """Normalize inputs"""
    return {
        "event_date": event_date,
        "headcount": headcount,
        "menu": menu,
        "capacity_ok": False,
        "ingredients_ok": False,
        "quote": {},
        "status": "pending",
        "reason": ""
    }

@tool
def check_capacity(capacity_ok: bool, headcount: int):
    """Verify kitchen & staff capacity"""
    return {"capacity_ok": headcount <= 150}

@tool
def check_ingredients(ingredients_ok: bool, menu: list):
    """Confirm bulk ingredients availability"""
    allowed_items = ["grilled chicken", "pasta primavera", "salad", "dessert"]
    return {"ingredients_ok": all(item in allowed_items for item in menu)}

@tool
def draft_quote(capacity_ok: bool, ingredients_ok: bool, headcount: int):
    """Compute price and timeline"""
    if capacity_ok and ingredients_ok:
        return {"quote": {"total": headcount*35, "per_person": 35, "ready_time": "16:00"}}
    return {"quote": {}}

@tool
def manager_gate(status: str, reason: str, quote: dict):
    """Manual approval by user"""
    print("\nQuote Preview:")
    print(json.dumps(quote, indent=2))
    while True:
        approval = input("Do you approve this quote? (yes/no): ").strip().lower()
        if approval in ["yes", "y"]:
            return {"status": "approved", "reason": ""}
        elif approval in ["no", "n"]:
            return {"status": "needs_revision", "reason": "insufficient grill capacity"}
        else:
            print("Please type 'yes' or 'no'.")

@tool
def finalize(status: str, quote: dict, reason: str):
    """Finalize workflow"""
    return {"status": status, "quote": quote, "reason": reason}


# sequential workflow
def run_catering_orchestrator_manual(input_data: dict):
    # Step 1: Capture the request
    state = capture_request.invoke(input={
        "event_date": input_data["event_date"],
        "headcount": input_data["headcount"],
        "menu": input_data["menu"]
    })

    # Step 2: Checking Capacity
    state.update(check_capacity.invoke(input={
        "capacity_ok": state["capacity_ok"],
        "headcount": state["headcount"]
    }))

    # Step 3: checking the Ingredients 
    state.update(check_ingredients.invoke(input={
        "ingredients_ok": state["ingredients_ok"],
        "menu": state["menu"]
    }))

    # Step 4: Drafting a quote
    state.update(draft_quote.invoke(input={
        "capacity_ok": state["capacity_ok"],
        "ingredients_ok": state["ingredients_ok"],
        "headcount": state["headcount"]
    }))

    # Step 5:  manager approval
    state.update(manager_gate.invoke(input={
        "status": state["status"],
        "reason": state["reason"],
        "quote": state["quote"]
    }))

    # Step 6: Finalize the request
    state.update(finalize.invoke(input={
        "status": state["status"],
        "quote": state["quote"],
        "reason": state["reason"]
    }))

    return state

# building the graph
def build_catering_graph():
    graph = StateGraph(CateringState)
    graph.add_node("capture_request", capture_request)
    graph.add_node("check_capacity", check_capacity)
    graph.add_node("check_ingredients", check_ingredients)
    graph.add_node("draft_quote", draft_quote)
    graph.add_node("manager_gate", manager_gate)
    graph.add_node("finalize", finalize)

    # Linear flow
    graph.add_edge(START, "capture_request")
    graph.add_edge("capture_request", "check_capacity")
    graph.add_edge("check_capacity", "check_ingredients")
    graph.add_edge("check_ingredients", "draft_quote")
    graph.add_edge("draft_quote", "manager_gate")
    graph.add_edge("manager_gate", "finalize")
    graph.add_edge("finalize", END)

    return graph.compile()

# running the main
if __name__ == "__main__":
    input_data = {
        "event_date": "2025-11-12",
        "headcount": 120,
        "menu": ["grilled chicken", "pasta primavera", "salad"]
    }

    
    final_state = run_catering_orchestrator_manual(input_data)
    print("\nFinal Catering State:")
    print(json.dumps(final_state, indent=2))

   
    print("\nWorkflow Graph:")
    orchestrator_graph = build_catering_graph()
    orchestrator_graph.get_graph().print_ascii()
