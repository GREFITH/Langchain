from typing import TypedDict

# class
class OrderSummary(TypedDict):
    route: str
    prep_eta_min: int | None
    courier_eta_min: int | None
    notes: str

# defining flows
def dine_in_flow(data: dict) -> OrderSummary:
    return {
        "route": "dine_in",
        "prep_eta_min": 10,
        "courier_eta_min": None,
        "notes": "Table 8 reserved",
    }


def takeout_flow(data: dict) -> OrderSummary:
    return {
        "route": "takeout",
        "prep_eta_min": 15,
        "courier_eta_min": None,
        "notes": "Pickup label printed",
    }


def delivery_flow(data: dict) -> OrderSummary:
    return {
        "route": "delivery",
        "prep_eta_min": 18,
        "courier_eta_min": 22,
        "notes": "Assigned to Driver-07",
    }

# defining router
def router(data: dict) -> OrderSummary | str:
    order_type = data.get("order_type")

    if order_type == "dine_in":
        return dine_in_flow(data)
    elif order_type == "takeout":
        return takeout_flow(data)
    elif order_type == "delivery":
        return delivery_flow(data)
    else:
        return "unsupported order type"

# running the main
if __name__ == "__main__":
    data = {
        "order_type": "delivery",
        "items": ["margherita pizza", "caesar salad"],
        "address": "55 King St W",
        "requested_time": "ASAP",
    }

    result = router(data)
    print(result)