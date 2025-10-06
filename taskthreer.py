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

# class
class OrderState(TypedDict):
    order_type: str
    items: list
    address: str
    requested_time: str
    route: str
    prep_eta_min: int
    courier_eta_min: int
    notes: str

# defining tools
@tool
def dine_in(order_type: str, items: list):
    """Handle dine-in orders"""
    return {
        "route": "dine_in",
        "prep_eta_min": 10,
        "courier_eta_min": 0,
        "notes": f"Table assigned, notify host for {len(items)} items"
    }

@tool
def takeout(order_type: str, items: list):
    """Handle takeout orders"""
    return {
        "route": "takeout",
        "prep_eta_min": 15,
        "courier_eta_min": 0,
        "notes": "Print pickup label"
    }

@tool
def delivery(order_type: str, items: list, address: str):
    """Handle delivery orders"""
    return {
        "route": "delivery",
        "prep_eta_min": 18,
        "courier_eta_min": 22,
        "notes": f"Assigned to driver for delivery to {address}"
    }

@tool
def unsupported(order_type: str):
    """Handle unsupported orders"""
    return {
        "route": "unsupported",
        "prep_eta_min": 0,
        "courier_eta_min": 0,
        "notes": f"Order type '{order_type}' is not supported"
    }

# routing function
def route_order(input_data: dict) -> dict:
    """
    Routes an incoming order to the proper path based on order_type.
    Returns a single summary matching task requirements.
    """
    order_type = input_data.get("order_type", "").lower()
    
    if order_type == "dine_in":
        return dine_in.invoke(input=input_data)
    elif order_type == "takeout":
        return takeout.invoke(input=input_data)
    elif order_type == "delivery":
        return delivery.invoke(input=input_data)
    else:
        return unsupported.invoke(input={"order_type": order_type})

# graphical part
def build_router_graph():
    graph = StateGraph(OrderState)
    graph.add_node("dine_in", dine_in)
    graph.add_node("takeout", takeout)
    graph.add_node("delivery", delivery)
    graph.add_node("unsupported", unsupported)

    # Routing edges from START
    graph.add_edge(START, "dine_in")
    graph.add_edge(START, "takeout")
    graph.add_edge(START, "delivery")
    graph.add_edge(START, "unsupported")

    # All nodes go to END after execution
    graph.add_edge("dine_in", END)
    graph.add_edge("takeout", END)
    graph.add_edge("delivery", END)
    graph.add_edge("unsupported", END)

    return graph.compile()

# running the router
if __name__ == "__main__":
    input_order = {
        "order_type": "delivery",
        "items": ["margherita pizza", "caesar salad"],
        "address": "55 King St W",
        "requested_time": "ASAP"
    }

   
    final_state = route_order(input_order)
    print("\nRouted Order Summary:")
    print(json.dumps(final_state, indent=2))

    
    print("\nOrder Routing Graph:")
    router_graph = build_router_graph()
    router_graph.get_graph().print_ascii()
