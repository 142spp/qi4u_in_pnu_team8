from fastapi import APIRouter, BackgroundTasks, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from .core.loader import get_all_lectures
from .services.task_manager import create_optimization_task, get_task_status
from .services.quantum_optimizer import optimize_timetable

router = APIRouter()

class OptimizationRequest(BaseModel):
    selected_lecture_ids: List[str]
    target_credits: Optional[float] = 21.0
    
    # Annealing configs
    use_quantum_annealing: Optional[bool] = False
    dwave_token: Optional[str] = None
    max_candidates: Optional[int] = 300
    total_reads: Optional[int] = 100
    batch_size: Optional[int] = 100
    
    # BQM Weights
    w_hard_overlap: Optional[float] = 10000.0
    w_target_credit: Optional[float] = 100.0
    w_mandatory: Optional[float] = -10000.0
    w_first_class: Optional[float] = 50.0
    w_lunch_overlap: Optional[float] = 30.0
    r_free_day: Optional[float] = 100.0
    p_free_day_break: Optional[float] = 500.0
    w_contiguous_reward: Optional[float] = -20.0
    w_tension_base: Optional[float] = 5.0

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
