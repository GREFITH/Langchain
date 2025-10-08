from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict
from typing import Dict, Any
import json
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

load_dotenv()


llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")  

# State
class CateringState(TypedDict, total=False):
    event_date: str
    headcount: int
    menu: list
    complexity: str
    capacity_ok: bool
    ingredients_ok: bool
    quote: Dict[str, Any]
    status: str
    reason: str

# Fucntions
def capture_request(state: Dict) -> Dict:
    return {
        "event_date": state.get("event_date"),
        "headcount": state.get("headcount", 0),
        "menu": state.get("menu", []),
        "complexity": "",
        "capacity_ok": False,
        "ingredients_ok": False,
        "quote": {},
        "status": "pending",
        "reason": ""
    }

def determine_complexity(state: Dict) -> Dict:
    headcount = state.get("headcount", 0)
    menu = state.get("menu", [])
    if headcount > 120 or any(item.lower() in ("lobster", "steak", "premium cake") for item in menu):
        level = "high"
    elif headcount > 60:
        level = "medium"
    else:
        level = "low"
    print(f"Complexity determined: {level}")
    return {"complexity": level}

def check_capacity(state: Dict) -> Dict:
    caps = {"low": 60, "medium": 120, "high": 250}
    cap = caps.get(state.get("complexity", "low"), 60)
    ok = state.get("headcount", 0) <= cap
    print(f"Capacity check ({state.get('headcount')} <= {cap}) -> {ok}")
    return {"capacity_ok": ok}

def check_ingredients(state: Dict) -> Dict:
    allowed = {"grilled chicken","pasta","salad","dessert","paneer tikka","naan","butter chicken","steak","lobster","premium cake"}
    menu = state.get("menu", [])
    ok = all(item.lower() in (a.lower() for a in allowed) for item in menu)
    print(f"Ingredients check -> {ok}")
    return {"ingredients_ok": ok}

def draft_low(state: Dict) -> Dict:
    rate = 28
    total = state["headcount"] * rate
    quote = {"total": total, "per_person": rate, "ready_time": "15:00"}
    print(f"Low draft: {quote}")
    return {"quote": quote}

def draft_medium(state: Dict) -> Dict:
    rate = 34
    total = state["headcount"] * rate
    quote = {"total": total, "per_person": rate, "ready_time": "16:00"}
    print(f"Medium draft: {quote}")
    return {"quote": quote}

def draft_high(state: Dict) -> Dict:
    rate = 48
    total = state["headcount"] * rate
    quote = {"total": total, "per_person": rate, "ready_time": "18:00"}
    print(f"High draft: {quote}")
    return {"quote": quote}

def manager_gate(state: Dict) -> Dict:
    """Manual manager approval with Gemini-generated reason"""
    quote = state.get("quote", {})
    if not quote:
        return {"status": "needs_revision", "reason": "infeasible request"}

    print("\nQuote for approval:")
    print(json.dumps(quote, indent=2))

    while True:
        ans = input("Approve quote? (yes/no): ").strip().lower()
        if ans in ("yes", "y", "no", "n"):
            prompt_template = ChatPromptTemplate.from_template("""
            You are a manager reviewing this catering request:
            {request}
            Decision: {decision}
            Generate a short reason explaining the decision.
            Respond JSON as {{"reason": "<short reason>"}}
            """)
            parser = JsonOutputParser()
            chain = prompt_template | llm | parser
            response = chain.invoke({
                "request": json.dumps(state),
                "decision": ans
            })
            status = "approved" if ans in ("yes","y") else "needs_revision"
            return {"status": status, "reason": response["reason"]}
        print("Please enter yes or no.")

def finalize_approved(state: Dict) -> Dict:
    return {"status": "approved", "quote": state.get("quote", {}), "reason": state.get("reason", "manager requested changes")}

def finalize_rejected(state: Dict) -> Dict:
    return {"status": "needs_revision", "quote": {}, "reason": state.get("reason", "manager requested changes")}

# Graph construction
def build_graph():
    graph = StateGraph(CateringState)

    graph.add_node("capture_request", capture_request)
    graph.add_node("determine_complexity", determine_complexity)
    graph.add_node("check_capacity", check_capacity)
    graph.add_node("check_ingredients", check_ingredients)
    graph.add_node("draft_low", draft_low)
    graph.add_node("draft_medium", draft_medium)
    graph.add_node("draft_high", draft_high)
    graph.add_node("manager_gate", manager_gate)
    graph.add_node("finalize_approved", finalize_approved)
    graph.add_node("finalize_rejected", finalize_rejected)

    graph.add_edge(START, "capture_request")
    graph.add_edge("capture_request", "determine_complexity")
    graph.add_edge("determine_complexity", "check_capacity")
    graph.add_edge("check_capacity", "check_ingredients")

    # branch to draft based on complexity
    graph.add_conditional_edges(
        "check_ingredients",
        lambda s: "draft_low" if s.get("complexity") == "low"
                  else "draft_medium" if s.get("complexity") == "medium"
                  else "draft_high",
        {
            "draft_low": "draft_low",
            "draft_medium": "draft_medium",
            "draft_high": "draft_high"
        }
    )

    graph.add_edge("draft_low", "manager_gate")
    graph.add_edge("draft_medium", "manager_gate")
    graph.add_edge("draft_high", "manager_gate")

    graph.add_conditional_edges(
        "manager_gate",
        lambda s: "finalize_approved" if s.get("status") == "approved" else "finalize_rejected",
        {
            "finalize_approved": "finalize_approved",
            "finalize_rejected": "finalize_rejected"
        }
    )

    graph.add_edge("finalize_approved", END)
    graph.add_edge("finalize_rejected", END)

    return graph.compile()

# running the main
if __name__ == "__main__":
    request = {
        "event_date": "2025-11-12",
        "headcount": 80,
        "menu": ["grilled chicken", "pasta", "salad"]
    }

    app = build_graph()
    print("\nWorkflow Graph (ASCII):")
    app.get_graph().print_ascii()

    print("\nRunning workflow — manual approval at manager gate with Gemini-generated reasons.\n")
    result = app.invoke(request)

    print("\nFinal aggregated result:")
    print(json.dumps(result, indent=2))
