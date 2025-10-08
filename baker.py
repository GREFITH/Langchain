import os
import time
import random
import json
from dotenv import load_dotenv
from typing import List, Dict, Any
from pydantic import BaseModel
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI

# Loading .env
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise SystemExit("ERROR: GOOGLE_API_KEY not set in environment")

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=GOOGLE_API_KEY)


# Structured state

class BakeState(BaseModel):
    item: str
    target_temp_c: int
    batch_size: int
    attempts: int = 0
    heartbeats: List[Dict[str, Any]] = []
    current_stage: str = ""
    status: str = "pending"  
    reason: str = ""
    peak_oven_c: int = 0
    stages: List[str] = []

# Worker

def bake_worker(state: BakeState) -> BakeState:
    stages = ["preheat", "load", "bake", "finish"]
    for stage in stages:
        state.current_stage = stage
        core_temp = random.randint(state.target_temp_c - 20, state.target_temp_c + 5)
        state.peak_oven_c = max(state.peak_oven_c, core_temp)
        hb = {"stage": stage, "core_temp_c": core_temp, "ok": core_temp >= state.target_temp_c - 15}
        state.heartbeats.append(hb)
        print(f"Heartbeat: {hb}")
        time.sleep(1)

        if random.random() < 0.08 or not hb["ok"]:
            state.stages = stages[: stages.index(stage) + 1]
            state.status = "failed"
            return state

    state.stages = stages
    state.status = "completed"
    return state

# Supervisor

def supervisor(state: BakeState) -> BakeState:
    max_attempts = 3
    while state.attempts < max_attempts:
        state.attempts += 1
        print(f"\nSupervisor: starting attempt #{state.attempts}")
        state = bake_worker(state)
        if state.status == "completed":
            prompt = (
                f"Bake completed successfully.\n"
                f"Item: {state.item}\nBatch size: {state.batch_size}\n"
                f"Peak oven temp: {state.peak_oven_c}°C\n"
                f"Provide a concise 1-2 sentence reason/summary for logs."
            )
            resp = llm.invoke(prompt)
            state.reason = (resp.content or "").strip()
            print(f"Supervisor: success reason from Gemini: {state.reason}")
            return state
        print(f"Supervisor: attempt #{state.attempts} failed, retrying...")
        time.sleep(1)

    
    prompt = (
        f"Bake aborted after {max_attempts} attempts.\n"
        f"Item: {state.item}\nBatch size: {state.batch_size}\n"
        f"Peak oven temp: {state.peak_oven_c}\n"
        f"Provide a concise reason suitable for escalation (1-2 sentences)."
    )
    resp = llm.invoke(prompt)
    state.status = "aborted"
    state.reason = (resp.content or "").strip()
    print(f"Supervisor: abort reason from Gemini: {state.reason}")
    return state

def finalize_success(state: BakeState) -> Dict[str, Any]:
    return state.dict()

def finalize_failure(state: BakeState) -> Dict[str, Any]:
    return state.dict()

# graph construction
def build_graph():
    graph = StateGraph(BakeState)
    graph.add_node("supervisor", supervisor)
    graph.add_node("finalize_success", finalize_success)
    graph.add_node("finalize_failure", finalize_failure)

    graph.add_edge(START, "supervisor")
    graph.add_conditional_edges(
        "supervisor",
        lambda s: "finalize_success" if s.status == "completed" else "finalize_failure",
        {"finalize_success": "finalize_success", "finalize_failure": "finalize_failure"}
    )
    graph.add_edge("finalize_success", END)
    graph.add_edge("finalize_failure", END)
    return graph.compile()

# running the main
if __name__ == "__main__":
    request = {"item": "sourdough", "target_temp_c": 230, "batch_size": 12}
    app = build_graph()

    print("\nWorkflow Graph (ASCII):")
    app.get_graph().print_ascii()

    print("\nRunning baking workflow...\n")
    result = app.invoke(request)

    print("\nFinal aggregated result:")
    print(json.dumps(result, indent=2))
