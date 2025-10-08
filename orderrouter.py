from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.messages import SystemMessage, HumanMessage
import json
import os
from dotenv import load_dotenv

#loading .env
load_dotenv()
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

# State
class OrderState(TypedDict, total=False):
    order_type: str
    items: List[str]
    address: str
    requested_time: str
    route: str
    prep_eta_min: int
    courier_eta_min: int
    notes: str

# FUNCTIONS

def intake_order(state: OrderState) -> OrderState:
    """Capture the order info and prepare for routing."""
    return OrderState(
        order_type=state.get("order_type"),
        items=state.get("items", []),
        address=state.get("address", ""),
        requested_time=state.get("requested_time", "")
    )

def route_order(state: OrderState) -> OrderState:
    """Use Gemini LLM to decide the routing based on order_type."""
    prompt = ChatPromptTemplate.from_template("""
        You are an order router. The order has the following info:
        {order_json}

        Decide the route based on order_type:
        - "dine_in": find table, estimate seat time, notify host
        - "takeout": estimate prep time, print pickup label
        - "delivery": estimate prep + courier ETA, assign driver
        - anything else: unsupported

        Respond ONLY in JSON:
        {{"route": "<dine_in|takeout|delivery|unsupported>"}}
    """)
    parser = JsonOutputParser()
    chain = prompt | llm | parser

    response = chain.invoke({"order_json": json.dumps(state)})
    state["route"] = response.get("route")
    return state


def handle_dine_in(state: OrderState) -> OrderState:
    """Dine-in path."""
    table_num = 7
    state.update({
        "prep_eta_min": 5,
        "notes": f"Table {table_num} ready, notify host"
    })
    return state

def handle_takeout(state: OrderState) -> OrderState:
    """Takeout path."""
    state.update({
        "prep_eta_min": 12,
        "notes": "Pickup label printed"
    })
    return state

def handle_delivery(state: OrderState) -> OrderState:
    """Delivery path."""
    state.update({
        "prep_eta_min": 18,
        "courier_eta_min": 22,
        "notes": "Assigned to Driver-07"
    })
    return state

def handle_unsupported(state: OrderState) -> OrderState:
    state["notes"] = f"Unsupported order type: {state.get('order_type')}"
    return state

# graph construction
def build_order_graph():
    graph = StateGraph(OrderState)

    
    graph.add_node("intake_order", intake_order)
    graph.add_node("route_order", route_order)
    graph.add_node("dine_in", handle_dine_in)
    graph.add_node("takeout", handle_takeout)
    graph.add_node("delivery", handle_delivery)
    graph.add_node("unsupported", handle_unsupported)

    
    graph.add_edge(START, "intake_order")
    graph.add_edge("intake_order", "route_order")

   
    graph.add_conditional_edges(
        "route_order",
        lambda s: s.get("route"),
        {
            "dine_in": "dine_in",
            "takeout": "takeout",
            "delivery": "delivery",
            "unsupported": "unsupported"
        }
    )

    
    graph.add_edge("dine_in", END)
    graph.add_edge("takeout", END)
    graph.add_edge("delivery", END)
    graph.add_edge("unsupported", END)

    return graph.compile()

# running the main
if __name__ == "__main__":
    request = {
        "order_type": "delivery",
        "items": ["margherita pizza", "caesar salad"],
        "address": "55 King St W",
        "requested_time": "ASAP"
    }

    app = build_order_graph()

    print("\nWorkflow Graph (ASCII):")
    app.get_graph().print_ascii()

    print("\nRunning order workflow...\n")
    result = app.invoke(request)

    print("\nFinal result:")
    print(json.dumps(result, indent=2))
