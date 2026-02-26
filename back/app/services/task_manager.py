import uuid
from typing import Dict, Any

# In-memory global task state storage
global_tasks_store: Dict[str, Any] = {}

def create_optimization_task(user_preferences: dict) -> str:
    """Creates a new task ID and intializes it in the store."""
    task_id = str(uuid.uuid4())
    global_tasks_store[task_id] = {
        "status": "PENDING",
        "summary": "Initializing...",
        "preferences": user_preferences,
        "result": None,
        "error": None
    }
    return task_id

def update_task_status(task_id: str, status: str, summary: str = None, result: Any = None, error: str = None):
    """Updates the status and optional result of a task."""
    if task_id in global_tasks_store:
        global_tasks_store[task_id]["status"] = status
        if summary is not None:
             global_tasks_store[task_id]["summary"] = summary
        if result is not None:
            global_tasks_store[task_id]["result"] = result
        if error is not None:
            global_tasks_store[task_id]["error"] = error
        print(f"STORE_UPDATE: Task {task_id} -> {status} ({summary or ''})")

def get_task_status(task_id: str) -> dict:
    """Retrieves the full task information."""
    return global_tasks_store.get(task_id, {"status": "NOT_FOUND"})
