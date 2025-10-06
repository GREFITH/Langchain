import os
import random
import time
from dotenv import load_dotenv
from typing_extensions import TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool

# loading .env
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise SystemExit("ERROR: GOOGLE_API_KEY not found in .env")

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=api_key)

#class
class BakeState(TypedDict):
    item: str
    target_temp_c: int
    batch_size: int
    status: str
    stages: list
    peak_oven_c: int
    attempts: int
    reason: str

#defining tool for worker
@tool
def bake_batch(item: str, target_temp_c: int, batch_size: int) -> dict:
    """
    Simulates baking stages with heartbeats. Randomly fails sometimes.
    """
    stages = ["preheat", "load", "bake", "finish"]
    peak_temp = 0

    for stage in stages:
        
        time.sleep(0.5)

     
        core_temp = random.randint(target_temp_c-10, target_temp_c+5)
        peak_temp = max(peak_temp, core_temp)

        
        heartbeat_ok = random.choice([True]*8 + [False]*2)  

        print(f"Stage: {stage}, core_temp: {core_temp}, heartbeat_ok: {heartbeat_ok}")

        if not heartbeat_ok or core_temp < target_temp_c - 5:
            
            return {"status": "failed", "reason": "no heartbeat / oven temp instability"}

    
    return {"status": "completed", "stages": stages, "peak_oven_c": peak_temp, "batch_size": batch_size}

#defining tool for superviosr
@tool
def supervise_bake(item: str, target_temp_c: int, batch_size: int, max_retries: int = 3) -> BakeState:
    """
    Supervises bake_batch with retries up to max_retries.
    """
    attempts = 0
    while attempts < max_retries:
        attempts += 1
        print(f"\n Attempt {attempts} for {item} batch")
        result = bake_batch.invoke(input={"item": item, "target_temp_c": target_temp_c, "batch_size": batch_size})
        
        if result["status"] == "completed":
            # Successful bake
            return {
                "item": item,
                "target_temp_c": target_temp_c,
                "batch_size": batch_size,
                "status": "completed",
                "stages": result["stages"],
                "peak_oven_c": result["peak_oven_c"],
                "attempts": attempts,
                "reason": ""
            }
        else:
            print(f" Bake failed: {result['reason']}")
            time.sleep(1)  

    #   ending or terminating  after max retries
    return {
        "item": item,
        "target_temp_c": target_temp_c,
        "batch_size": batch_size,
        "status": "aborted",
        "stages": [],
        "peak_oven_c": 0,
        "attempts": attempts,
        "reason": "no heartbeat / oven temp instability"
    }

# running the supervisor
if __name__ == "__main__":
    input_data = {
        "item": "sourdough",
        "target_temp_c": 230,
        "batch_size": 12
    }

    final_state = supervise_bake.invoke(input=input_data)
    print("\n Final Bake State:")
    from pprint import pprint
    pprint(final_state)
