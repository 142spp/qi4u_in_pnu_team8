import time
import re
import math
from .task_manager import update_task_status
from ..core.loader import get_lecture_by_id
from ..utils.time_utils import parse_time_to_range
from .bqm_builder import build_timetable_bqm

try:
    import dimod
except ImportError:
    pass


def optimize_timetable(task_id: str, preferences: dict):
    """
    Background worker function that builds the BQM and solves it via Simulated Annealing.
    """
    try:
        update_task_status(task_id, "PROCESSING")
        
        selected_ids = preferences.get("selected_lecture_ids", [])
        if not selected_ids:
            raise ValueError("No lectures provided for optimization.")
            
        print(f"Task {task_id}: Preparing QUBO for {len(selected_ids)} lectures.")
        
        # 1. Fetch Lecture Details and Parse Times
        lectures = []
        for lid in selected_ids:
            lec = get_lecture_by_id(lid)
            if lec:
                lec_copy = lec.copy()
                lec_copy['parsed_time'] = parse_time_to_range(lec['time_room'])
                lectures.append(lec_copy)
        
        N = len(lectures)
        if N == 0:
             raise ValueError("None of the selected lectures were found in the database.")
        
        # 2. Build BQM using our algorithmic logic
        bqm = build_timetable_bqm(lectures, preferences)

        # 3. Submit to Simulated Annealing Sampler
        print(f"Task {task_id}: Solving BQM using Simulated Annealing...")
        sampler = dimod.SimulatedAnnealingSampler()
        # Num reads determines how many times we run the simulated annealing (more = better chance of finding global min)
        sampleset = sampler.sample(bqm, num_reads=500)
        
        # 4. Parse Results
        best_sample = sampleset.first.sample
        energy = sampleset.first.energy
        
        final_schedule = []
        # Exclude auxiliary variables such as y_d (free_월, free_화...)
        for var_name, is_selected in best_sample.items():
            if is_selected == 1 and not str(var_name).startswith("free_"):
                lec = get_lecture_by_id(var_name)
                if lec:
                    final_schedule.append(lec)

        # Basic Check: Calculate total credits for logging
        total_credits_found = sum(lec['credit'] for lec in final_schedule)
        print(f"Task {task_id}: Optimization complete. Selected {len(final_schedule)} lectures ({total_credits_found} credits). Energy: {energy}")
        
        # Update status
        update_task_status(task_id, "SUCCESS", result={
            "schedule": final_schedule,
            "energy": energy,
            "total_credits": total_credits_found
        })

    except Exception as e:
        print(f"Task {task_id} Failed: {str(e)}")
        update_task_status(task_id, "FAILURE", error=str(e))

