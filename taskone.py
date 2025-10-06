import asyncio
from typing import TypedDict

# class
class DinnerSnapshot(TypedDict):
    inventory: dict
    floor: dict
    delivery: dict
    overall: str

# defining async tools
async def check_inventory(service_area: str) -> dict:
    await asyncio.sleep(1)
    return {"steak": "low", "pasta": "ok", "lettuce": "ok"}


async def check_floor(service_area: str) -> dict:
    await asyncio.sleep(1.5)
    return {"open_tables": 4, "waitlist": 12}


async def check_delivery(service_area: str) -> dict:
    await asyncio.sleep(1.2)
    return {"drivers_on_duty": 5, "avg_eta_min": 28}


async def dinner_rush_snapshot(inputs: dict) -> DinnerSnapshot:
    service_area = inputs["service_area"]

    inventory_task = check_inventory(service_area)
    floor_task = check_floor(service_area)
    delivery_task = check_delivery(service_area)

    inventory, floor, delivery = await asyncio.gather(
        inventory_task, floor_task, delivery_task
    )

    overall = "busy" if floor["waitlist"] > 10 else "normal"

    return {
        "inventory": inventory,
        "floor": floor,
        "delivery": delivery,
        "overall": overall,
    }

# running the main
if __name__ == "__main__":
    inputs = {"service_area": "downtown"}
    result = asyncio.run(dinner_rush_snapshot(inputs))
    print(result)