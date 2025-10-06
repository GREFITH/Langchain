import asyncio
import random
from typing import TypedDict

# class
class BakeResult(TypedDict):
    status: str
    stages: list[str] | None
    peak_oven_c: int | None
    batch_size: int | None
    reason: str | None
    attempts: int

# defining async baker
async def bake_batch(data: dict) -> dict:
    stages = ["preheat", "load", "bake", "finish"]
    for stage in stages:
        await asyncio.sleep(1)
        temp = random.randint(180, 240)
        print(f"Heartbeat: stage={stage}, core_temp={temp}")
        if temp < 200:
            raise Exception("Temp drop detected")
    return {"stages": stages, "peak_oven_c": random.randint(230, 235)}

#defining async supervisor 
async def supervisor(data: dict) -> BakeResult:
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            print(f"Attempt {attempt} starting...")
            result = await bake_batch(data)
            print("Bake success!")
            return {
                "status": "completed",
                **result,
                "batch_size": data["batch_size"],
                "reason": None,
                "attempts": attempt,
            }
        except Exception as e:
            print(f"Attempt {attempt} failed: {e}")
            if attempt == max_retries:
                return {
                    "status": "aborted",
                    "stages": None,
                    "peak_oven_c": None,
                    "batch_size": data["batch_size"],
                    "reason": str(e),
                    "attempts": attempt,
                }
            await asyncio.sleep(2)
            print("Retrying...")

# Running the main
if __name__ == "__main__":
    data = {"item": "sourdough", "target_temp_c": 230, "batch_size": 12}
    result = asyncio.run(supervisor(data))
    print(result)