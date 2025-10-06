from typing import TypedDict

#class
class CateringQuote(TypedDict):
    status: str
    quote: dict | None
    reason: str | None

# capturing and checking the nodes
def capture_request(data: dict) -> dict:
    print("Captured request:", data)
    return data


def check_capacity(data: dict) -> bool:
    return data["headcount"] <= 150


def check_ingredients(data: dict) -> bool:
    menu = data["menu"]
    return "pasta primavera" in menu


def draft_quote(data: dict) -> dict:
    per_person = 35
    total = per_person * data["headcount"]
    return {"total": total, "per_person": per_person, "ready_time": "16:00"}


def manager_gate(quote: dict) -> str:
    print("Quote proposal:", quote)
    decision = input("Approve this quote? (yes/no): ").strip().lower()
    return "approve" if decision == "yes" else "reject"


def finalize(data: dict, status: str, quote: dict | None = None) -> CateringQuote:
    if status == "approve":
        return {"status": "approved", "quote": quote, "reason": None}
    else:
        return {
            "status": "needs_revision",
            "quote": None,
            "reason": "insufficient grill capacity",
        }

# combining all nodes
def catering_orchestrator(data: dict) -> CateringQuote:
    capture_request(data)

    if not check_capacity(data):
        return finalize(data, "reject")

    if not check_ingredients(data):
        return finalize(data, "reject")

    quote = draft_quote(data)
    decision = manager_gate(quote)
    return finalize(data, decision, quote)

# running the main
if __name__ == "__main__":
    data = {
        "event_date": "2025-11-12",
        "headcount": 120,
        "menu": ["grilled chicken", "pasta primavera", "salad"],
    }

    result = catering_orchestrator(data)
    print(result)