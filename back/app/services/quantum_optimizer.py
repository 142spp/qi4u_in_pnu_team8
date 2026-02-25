import time
from .task_manager import update_task_status
from ..core.loader import get_lecture_by_id

# Use dimod's Simulated Annealing instead of actual D-Wave hardware
try:
    import dimod
except ImportError:
    pass

def parse_time_string(time_str: str):
    """
    Dummy parser to extract days and times from '수 09:00-12:00, 토 14:00-17:00' format
    For the real BQM, this would map time blocks to discrete indices (e.g. Mon 09:00 -> 0)
    """
    # Simple prototype implementation: just return raw string or basic blocks
    return time_str.split(",")

def optimize_timetable(task_id: str, preferences: dict):
    """
    Background worker function that builds the BQM and solves it via Simulated Annealing.
    """
    try:
        update_task_status(task_id, "PROCESSING")
        
        selected_ids = preferences.get("selected_lecture_ids", [])
        if not selected_ids:
            raise ValueError("No lectures provided for optimization.")
            
        print(f"Task {task_id}: Preparing QUBO for {len(selected_ids)} lectures")
        
        # 1. Fetch Lecture Details
        lectures = [get_lecture_by_id(lid) for lid in selected_ids if get_lecture_by_id(lid)]
        
        # 2. Build BQM
        # Variables: x_i (1 if lecture i is scheduled, 0 otherwise)
        bqm = dimod.BinaryQuadraticModel('BINARY')
        
        # Prototype Hard Constraints (Time Overlap)
        # For prototype simplicity, we do a naive check if strings overlap exactly
        for i in range(len(lectures)):
            # We add a small reward for including a class
            bqm.add_variable(lectures[i]["id"], -1.0)
            
            for j in range(i + 1, len(lectures)):
                # If times overlap, add a huge penalty
                # Example: If they share the exact same raw time string (very naive)
                if lectures[i]["time_room"] != "" and (lectures[i]["time_room"] == lectures[j]["time_room"]):
                    bqm.add_interaction(lectures[i]["id"], lectures[j]["id"], 10.0)

        # 3. Submit to Simulated Annealing Sampler
        print(f"Task {task_id}: Solving BQM using Simulated Annealing...")
        
        sampler = dimod.SimulatedAnnealingSampler()
        sampleset = sampler.sample(bqm, num_reads=100)
        
        # 4. Parse Results
        best_sample = sampleset.first.sample
        energy = sampleset.first.energy
        
        final_schedule = []
        for lec_id, is_selected in best_sample.items():
            if is_selected == 1:
                lec = get_lecture_by_id(lec_id)
                final_schedule.append(lec)

        print(f"Task {task_id}: Optimization complete. Selected {len(final_schedule)} lectures.")
        
        # Update status
        update_task_status(task_id, "SUCCESS", result={
            "schedule": final_schedule,
            "energy": energy
        })

    except Exception as e:
        print(f"Task {task_id} Failed: {str(e)}")
        update_task_status(task_id, "FAILURE", error=str(e))
