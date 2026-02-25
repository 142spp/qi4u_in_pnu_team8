from fastapi import APIRouter, BackgroundTasks, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from .core.loader import get_all_lectures
from .services.task_manager import create_optimization_task, get_task_status
from .services.quantum_optimizer import optimize_timetable

router = APIRouter()

class OptimizationRequest(BaseModel):
    selected_lecture_ids: List[str]
    max_credits: Optional[float] = 21.0
    prefer_contiguous: Optional[bool] = True
    prefer_free_days: Optional[bool] = False

@router.get("/lectures")
def get_lectures():
    """Returns the list of all available lectures."""
    lectures = get_all_lectures()
    if not lectures:
        raise HTTPException(status_code=500, detail="Lectures not loaded properly.")
    return {"lectures": lectures}

@router.post("/optimize")
def start_optimization(request: OptimizationRequest, background_tasks: BackgroundTasks):
    """Submits a timetable optimization task to run in the background."""
    if not request.selected_lecture_ids:
        raise HTTPException(status_code=400, detail="No lectures selected.")
        
    preferences = request.dict()
    task_id = create_optimization_task(preferences)
    
    # Offload the heavy quantum computation to a background task
    background_tasks.add_task(optimize_timetable, task_id, preferences)
    
    return {"task_id": task_id, "status": "PENDING"}

@router.get("/optimize/{task_id}")
def check_optimization_status(task_id: str):
    """Checks the status of a previously submitted optimization task."""
    status_info = get_task_status(task_id)
    if status_info["status"] == "NOT_FOUND":
        raise HTTPException(status_code=404, detail="Task not found")
    
    return status_info
