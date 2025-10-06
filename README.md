# Restaurant Workflow Automation — Python & LangChain/Tools Demo

This repository demonstrates **four sample workflows** for restaurant operations using **simple Python scripts** and **LangChain Tools / structure response-based workflows**. The project is divided into two approaches:

1. **Simple Python scripts** using nodes & edges for workflow representation.
2. **Tool-based structured response workflows** integrating LangChain + Gemini API.

---

## **Project Structure**

### **Task 1 — Parallelism: Dinner Rush Snapshot**
- **Purpose:** Quickly check restaurant status and return a single summary.
- **Simple Python version:** `task1_nodes.py`  
  Uses **nodes & edges** to simulate three parallel checks: inventory, floor, and delivery.
- **Tool-based version:** `taskonep.py`  
  Uses **LangChain tools + Gemini LLM** with structured responses to perform checks concurrently and merge results.

---

### **Task 2 — Orchestrator: Catering Request → Feasibility → Quote → Approval**
- **Purpose:** Linear workflow to process catering requests with human approval.
- **Simple Python version:** `task2_orchestrator_nodes.py`  
  Implements **nodes & edges**, showing steps: capture request → check capacity → check ingredients → draft quote → manager approval → finalize.
- **Tool-based version:** `tasktwoo.py`  
  Implements the same workflow using **LangChain tools + structure response**, simulating human approval as an interrupt.

---

### **Task 3 — Router: Order Intake Triage**
- **Purpose:** Route incoming orders to the correct handling path based on order type.
- **Simple Python version:** `task3_router_nodes.py`  
  Uses nodes & edges to handle dine-in, takeout, delivery, or unsupported orders.
- **Tool-based version:** `taskthreer.py`  
  Uses **structured response tools** to route the order and return actionable summaries.

---

### **Task 4 — Supervisor: Oven Bake with Heartbeats & Auto-Retry**
- **Purpose:** Monitor baking workflow, retry on failures, abort on repeated failures.
- **Simple Python version:** `task4_supervisor_nodes.py`  
  Implements a **looping retry mechanism** using nodes & edges.
- **Tool-based version:** `taskfourr.py`  
  Uses **LangChain structured tools** to simulate heartbeats, failures, and retries.

---

## **Features**
- Node & edge based workflow representation.
- Structured response handling using LangChain + Gemini API.
- Supports parallelism, linear orchestration, routing, and retry logic.
- Simple Python scripts for easy understanding and testing.

---

## **Setup Instructions**

1. Clone the repository:

```bash
git clone <your-repo-url>
cd <your-repo-folder>
