import re
import math
import random
from .task_manager import update_task_status
from ..core.loader import get_lecture_by_id, get_all_lectures
from ..utils.time_utils import parse_time_to_range
from .bqm_builder import build_timetable_bqm

import dimod
try:
    import neal
except ImportError:
    neal = None

def optimize_timetable(task_id: str, preferences: dict):
    """
    Background worker function that builds the BQM and solves it via Simulated Annealing.
    """
    try:
        update_task_status(task_id, "PROCESSING")
        
        selected_ids = preferences.get("selected_lecture_ids", [])
        if not selected_ids:
            raise ValueError("No lectures provided for optimization.")
            
        # Treat manually selected IDs as mandatory for the BQM
        preferences["mandatory_ids"] = selected_ids
            
        print(f"Task {task_id}: Preparing QUBO over all lectures with {len(selected_ids)} mandatory selections.")
        
        # 1. Fetch ALL Lecture Details and Parse Times
        all_lectures_data = get_all_lectures()
        
        # Performance Guard: Now scaled up to 1000 thanks to Neal (C++).
        # 1000 candidates provide a very rich search space while completing in seconds.
        MAX_CANDIDATES = preferences.get("max_candidates", 300)
        candidate_pool = []
        mandatory_pool = []
        for lec in all_lectures_data:
            if lec["id"] in selected_ids:
                mandatory_pool.append(lec)
            else:
                candidate_pool.append(lec)
        
        # Shuffle candidates for variety
        random.shuffle(candidate_pool)
        
        # Final set = all mandatory + subset of candidates
        final_pool = mandatory_pool + candidate_pool[:(MAX_CANDIDATES - len(mandatory_pool))]
        
        lectures = []
        for lec in final_pool:
            lec_copy = lec.copy()
            lec_copy['parsed_time'] = parse_time_to_range(lec['time_room'])
            lectures.append(lec_copy)
        
        N = len(lectures)
        if N == 0:
             raise ValueError("None of the selected lectures were found in the database.")
        
        # 2. Build BQM using our algorithmic logic
        def bqm_progress(msg, pct):
            update_task_status(task_id, "PROCESSING", summary=f"Building BQM: {msg} ({pct}%)")

        bqm = build_timetable_bqm(lectures, preferences, progress_callback=bqm_progress)

        # 3. Submit to Simulated Annealing Sampler (Batch Processing)
        print(f"Task {task_id}: Solving BQM using C++ Neal Sampler (Batched)...")
        
        if neal:
            sampler = neal.SimulatedAnnealingSampler()
        else:
            sampler = dimod.SimulatedAnnealingSampler()
            
        TOTAL_READS = preferences.get("total_reads", 100)
        BATCH_SIZE = preferences.get("batch_size", 100)
        
        # Ensure minimums
        if BATCH_SIZE <= 0: BATCH_SIZE = 100
        if TOTAL_READS <= 0: TOTAL_READS = 100
        
        num_batches = max(1, TOTAL_READS // BATCH_SIZE)
        
        all_samplesets = []
        for b in range(num_batches):
            progress_pct = int(((b + 1) / num_batches) * 100)
            update_task_status(task_id, "PROCESSING", summary=f"Quantum Optimization in progress... ({progress_pct}%)")
            
            # Perform batch sampling
            batch_sampleset = sampler.sample(bqm, num_reads=BATCH_SIZE)
            all_samplesets.append(batch_sampleset)
            
        # Concatenate all results
        sampleset = dimod.concatenate(all_samplesets)
        
        # 4. Parse Top 5 Unique Results
        # sampleset is ordered from lowest energy to highest
        top_schedules = []
        seen_combinations = set()
        
        for sample, energy in sampleset.data(['sample', 'energy']):
            if len(top_schedules) >= 5:
                break
                
            current_schedule = []
            current_ids = []
            
            # Exclude auxiliary variables such as y_d (free_월, free_화...)
            for var_name, is_selected in sample.items():
                if is_selected == 1 and not str(var_name).startswith("free_"):
                    lec = get_lecture_by_id(var_name)
                    if lec:
                        lec_dict = lec.copy()
                        lec_dict['parsed_time'] = parse_time_to_range(lec['time_room'])
                        current_schedule.append(lec_dict)
                        current_ids.append(lec['id'])
            
            # Create a unique signature for this schedule combination
            combo_sig = frozenset(current_ids)
            if combo_sig not in seen_combinations and len(current_schedule) > 0:
                seen_combinations.add(combo_sig)
                
                # Basic Check: Calculate total credits for logging
                total_credits_found = sum(lec['credit'] for lec in current_schedule)
                
                # Manual Breakdown Energy calculation
                breakdown = {
                    "credit_penalty": 0.0,
                    "1st_period_penalty": 0.0,
                    "lunch_overlap_penalty": 0.0,
                    "free_day_reward": 0.0,
                    "overlap_penalty": 0.0,
                    "contiguous_reward": 0.0,
                    "tension_penalty": 0.0,
                    "mandatory_reward": 0.0,
                    "time_credit_mismatch_penalty": 0.0,
                }
                
                # Recalculate based on preferences weights
                T_CREDIT = preferences.get("target_credits", 21.0)
                W_CREDIT = preferences.get("w_target_credit", 100.0)
                W_FIRST = preferences.get("w_first_class", 50.0)
                W_LUNCH = preferences.get("w_lunch_overlap", 30.0)
                R_FREE = preferences.get("r_free_day", 100.0)
                P_FREE_BREAK = preferences.get("p_free_day_break", 500.0)
                W_OVERLAP = preferences.get("w_hard_overlap", 10000.0)
                W_CONTIG = preferences.get("w_contiguous_reward", -20.0)
                W_TENSION = preferences.get("w_tension_base", 5.0)
                W_MAN = preferences.get("w_mandatory", -10000.0)
                W_TIME_CREDIT = preferences.get("w_time_credit_ratio", 50.0)
                
                breakdown["credit_penalty"] = round(W_CREDIT * (total_credits_found - T_CREDIT)**2, 2)
                
                days_with_classes = set()
                for lec in current_schedule:
                    if lec["id"] in selected_ids:
                        breakdown["mandatory_reward"] += W_MAN
                    
                    total_duration_minutes = 0
                    for pt in lec.get('parsed_time', []):
                        days_with_classes.add(pt['day'])
                        total_duration_minutes += (pt['end'] - pt['start'])
                        if pt['start'] <= 570:
                            breakdown["1st_period_penalty"] += W_FIRST
                        if max(pt['start'], 720) < min(pt['end'], 780):
                            breakdown["lunch_overlap_penalty"] += W_LUNCH
                            
                    duration_hours = total_duration_minutes / 60.0
                    if duration_hours > lec['credit']:
                        breakdown["time_credit_mismatch_penalty"] += round(W_TIME_CREDIT * (duration_hours - lec['credit']), 2)
                            
                # Free day logical reward
                for d in ['월', '화', '수', '목', '금', '토', '일']:
                    if f"free_{d}" in sample and sample[f"free_{d}"] == 1:
                        breakdown["free_day_reward"] += -R_FREE
                        if d in days_with_classes:
                            breakdown["free_day_reward"] += P_FREE_BREAK

                # Pairwise penalties
                for i in range(len(current_schedule)):
                    for j in range(i+1, len(current_schedule)):
                        lec_i = current_schedule[i]
                        lec_j = current_schedule[j]
                        
                        for pt_i in lec_i.get('parsed_time', []):
                            for pt_j in lec_j.get('parsed_time', []):
                                if pt_i['day'] == pt_j['day']: # Same day only
                                    from ..utils.time_utils import check_overlap, calculate_time_gap
                                    if check_overlap([pt_i], [pt_j]):
                                        breakdown["overlap_penalty"] += W_OVERLAP
                                    else:
                                        gap = calculate_time_gap([pt_i], [pt_j])
                                        if 0 < gap <= 60:
                                            breakdown["contiguous_reward"] += W_CONTIG
                                        elif 60 < gap <= 180:
                                            breakdown["tension_penalty"] += round(W_TENSION * math.sqrt(gap), 2)
                
                top_schedules.append({
                    "schedule": current_schedule,
                    "energy": energy,
                    "total_credits": total_credits_found,
                    "breakdown": breakdown
                })

        if not top_schedules:
            raise ValueError("No valid schedules could be generated.")
            
        best_result = top_schedules[0]
        print(f"Task {task_id}: Optimization complete. Found {len(top_schedules)} unique schedules. Best Energy: {best_result['energy']}")
        
        # Update status with Top 5
        update_task_status(task_id, "SUCCESS", result={
            "schedule": best_result["schedule"], # Keep for backward compatibility
            "energy": best_result["energy"],
            "total_credits": best_result["total_credits"],
            "breakdown": best_result["breakdown"],
            "top_schedules": top_schedules
        })

    except Exception as e:
        print(f"Task {task_id} Failed: {str(e)}")
        update_task_status(task_id, "FAILURE", error=str(e))

