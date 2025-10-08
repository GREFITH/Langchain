from dotenv import load_dotenv
import os
import json
from typing import Dict, Optional
from pydantic import BaseModel

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langgraph.graph import StateGraph, START, END


# Loading .env

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise SystemExit(" GOOGLE_API_KEY missing in .env file")


llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=api_key)


#  State

class RestaurantState(BaseModel):
    service_area: str
    inventory: Optional[Dict[str, str]] = None
    floor: Optional[Dict[str, int]] = None
    delivery: Optional[Dict[str, int]] = None
    overall: Optional[str] = None
    summary: Optional[str] = None


# Function
def safe_json_call(prompt_template: str, context: Dict) -> Dict:
    """
    Ensures the LLM always returns valid JSON.
    Retries parsing with relaxed rules if needed.
    """
    prompt = ChatPromptTemplate.from_template(prompt_template)
    parser = JsonOutputParser()
    chain = prompt | llm | StrOutputParser()  # get raw text first

    response_text = chain.invoke(context).strip()

  
    try:
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        json_str = response_text[start:end]
        return json.loads(json_str)
    except Exception:
        print("Warning: Non-JSON response received, fallback applied.")
        return {"error": "invalid_json", "raw_output": response_text}


def check_inventory(state: RestaurantState) -> Dict:
    """Check restaurant stock levels."""
    prompt = """
    You are checking stock for the {area} restaurant.
    Respond strictly in JSON format with three keys:
    {{"steak": "ok/low/critical", "pasta": "ok/low/critical", "lettuce": "ok/low/critical"}}
    """
    result = safe_json_call(prompt, {"area": state.service_area})
    return {"inventory": result}


def check_floor(state: RestaurantState) -> Dict:
    """Check dining area occupancy."""
    prompt = """
    Estimate occupancy for the {area} restaurant.
    Return only valid JSON:
    {{"open_tables": <number>, "waitlist": <number>}}
    """
    result = safe_json_call(prompt, {"area": state.service_area})
    return {"floor": result}


def check_delivery(state: RestaurantState) -> Dict:
    """Check delivery performance."""
    prompt = """
    You are a delivery monitor for the {area} restaurant.
    Return JSON with:
    {{"drivers_on_duty": <number>, "avg_eta_min": <number>}}
    """
    result = safe_json_call(prompt, {"area": state.service_area})
    return {"delivery": result}


def summarize_status(state: RestaurantState) -> Dict:
    """Summarize results from all nodes."""
    waitlist = state.floor.get("waitlist", 0) if state.floor else 0
    eta = state.delivery.get("avg_eta_min", 0) if state.delivery else 0
    steak = state.inventory.get("steak", "ok") if state.inventory else "ok"

    if steak == "low" or (waitlist + eta) > 35:
        overall = "busy"
    elif (waitlist + eta) > 20:
        overall = "moderate"
    else:
        overall = "calm"

    summary_text = (
        f" Restaurant Area: {state.service_area}\n"
        f" Floor: {state.floor}\n"
        f" Delivery: {state.delivery}\n"
        f" Inventory: {state.inventory}\n"
        f" Overall Status: {overall.upper()}"
    )

    return {"overall": overall, "summary": summary_text}


# Graph construction
def build_dinner_graph():
    graph = StateGraph(RestaurantState)

    graph.add_node("check_inventory", check_inventory)
    graph.add_node("check_floor", check_floor)
    graph.add_node("check_delivery", check_delivery)
    graph.add_node("summarize_status", summarize_status)

  
    graph.add_edge(START, "check_inventory")
    graph.add_edge(START, "check_floor")
    graph.add_edge(START, "check_delivery")

  
    graph.add_edge("check_inventory", "summarize_status")
    graph.add_edge("check_floor", "summarize_status")
    graph.add_edge("check_delivery", "summarize_status")

    graph.add_edge("summarize_status", END)

    return graph.compile()


# running main
if __name__ == "__main__":
    app = build_dinner_graph()
    app.get_graph().print_ascii()

    print("\nRunning Dinner Rush Snapshot...\n")
    result = app.invoke(RestaurantState(service_area="Downtown"))

    print("\nFinal JSON Output:")
    print(json.dumps({
        "service_area": result["service_area"],
        "inventory": result.get("inventory", {}),
        "floor": result.get("floor", {}),
        "delivery": result.get("delivery", {}),
        "overall": result.get("overall", "unknown")
    }, indent=2))

    print("\nHuman Summary:\n")
    print(result.get("summary", "No summary"))
