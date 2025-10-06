
from dotenv import load_dotenv
import os
import json
import asyncio
from typing_extensions import TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_core.runnables import RunnableParallel

# loading .env
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise SystemExit("ERROR: GOOGLE_API_KEY not found in .env")

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=api_key)

# class 
class RestaurantState(TypedDict):
    service_area: str
    inventory: dict
    floor: dict
    delivery: dict
    overall: str

# defining tools 
@tool
def check_inventory(service_area: str):
    """Check stock for key items: steak, pasta, lettuce"""
    inventory = {"steak": "low", "pasta": "ok", "lettuce": "ok"}
    return {"inventory": inventory}

@tool
def check_floor(service_area: str):
    """Check open tables and waitlist length"""
    floor = {"open_tables": 4, "waitlist": 12}
    return {"floor": floor}

@tool
def check_delivery(service_area: str):
    """Check active drivers and average ETA"""
    delivery = {"drivers_on_duty": 5, "avg_eta_min": 28}
    return {"delivery": delivery}

# parallel execution
async def dinner_rush_snapshot(service_area: str):
    parallel = RunnableParallel(
        inventory=lambda _: check_inventory(service_area),
        floor=lambda _: check_floor(service_area),
        delivery=lambda _: check_delivery(service_area)
    )

    results = await parallel.ainvoke({})
    
    # Summary by using gemini
    prompt = f"""
    Given the following restaurant status:
    {json.dumps(results, indent=2)}
    Return a single word for overall busyness: calm, moderate, busy, very busy.
    """
    overall = llm.invoke(prompt).content.strip() or "busy"
    results["overall"] = overall
    return results

# graphical nodes
def print_graph_nodes_edges():
    nodes = [
        {"id": "A", "label": "Check Inventory"},
        {"id": "B", "label": "Check Floor"},
        {"id": "C", "label": "Check Delivery"},
        {"id": "D", "label": "Merge Results"},
        {"id": "E", "label": "Overall Status"}
    ]
    edges = [("A","D"), ("B","D"), ("C","D"), ("D","E")]

    print("\nGraph Representation (Nodes & Edges):")
    print("Nodes:")
    for node in nodes:
        print(f"  {node['id']}: {node['label']}")
    print("Edges:")
    for src,dst in edges:
        print(f"  {src} -> {dst}")

# running the task
async def run_task1():
    input_data = {"service_area": "downtown"}
    print(f"\nInput:\n{json.dumps(input_data, indent=2)}")

    result = await dinner_rush_snapshot(input_data["service_area"])
    print("\nFinal Restaurant Snapshot:")
    print(json.dumps(result, indent=2))

    print_graph_nodes_edges()

if __name__ == "__main__":
    asyncio.run(run_task1())
