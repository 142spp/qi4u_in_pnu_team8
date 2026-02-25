import math
from ..utils.time_utils import check_overlap, calculate_time_gap

try:
    import dimod
except ImportError:
    pass

def build_timetable_bqm(lectures, preferences, progress_callback=None):
    """
    Builds the Binary Quadratic Model (BQM) for timetable optimization based on Hard and Soft constraints.
    Optimized to O(N_day^2) by grouping by day.
    """
    bqm = dimod.BinaryQuadraticModel('BINARY')
    
    # Extract preferences
    target_credits = preferences.get("target_credits", 21.0)
    mandatory_ids = preferences.get("mandatory_ids", [])
    
    N = len(lectures)
    
    # -------------------------------------------------------------------------
    # 0. Base Weights / Penalties Definitions
    # -------------------------------------------------------------------------
    W_HARD_OVERLAP = preferences.get("w_hard_overlap", 10000.0)
    W_TARGET_CREDIT = preferences.get("w_target_credit", 100.0)
    W_MANDATORY = preferences.get("w_mandatory", -10000.0)
    
    # Soft constraints - Linear
    W_FIRST_CLASS = preferences.get("w_first_class", 50.0)
    W_LUNCH_OVERLAP = preferences.get("w_lunch_overlap", 30.0)
    
    # Soft constraints - Free Days
    R_FREE_DAY = preferences.get("r_free_day", 100.0)
    P_FREE_DAY_BREAK = preferences.get("p_free_day_break", 500.0)
    
    # Soft constraints - Tension Model
    W_CONTIGUOUS_REWARD = preferences.get("w_contiguous_reward", -20.0)
    W_TENSION_BASE = preferences.get("w_tension_base", 5.0)
    
    # Soft constraints - Time/Credit Mismatch
    W_TIME_CREDIT_RATIO = preferences.get("w_time_credit_ratio", 50.0)
    
    linear_biases = {}
    quadratic_biases = {}
    
    def add_linear(var, bias):
        linear_biases[var] = linear_biases.get(var, 0.0) + bias
        
    def add_quadratic(u, v, bias):
        if str(u) > str(v): 
            u, v = v, u
        quadratic_biases[(u, v)] = quadratic_biases.get((u, v), 0.0) + bias

    # -------------------------------------------------------------------------
    # 1. Linear Biases & Day Grouping
    # -------------------------------------------------------------------------
    if progress_callback:
        progress_callback("Analyzing lectures and linear biases...", 10)

    # Group lectures by day for O(N_day^2) quadratic checks
    lectures_by_day = {d: [] for d in ['월', '화', '수', '목', '금', '토', '일']}
    
    for i in range(N):
        lec_i = lectures[i]
        id_i = lec_i["id"]
        c_i = lec_i["credit"]
        
        # Target Credit Linear Term
        add_linear(id_i, W_TARGET_CREDIT * (c_i**2 - 2 * target_credits * c_i))
        
        # Mandatory Requirement
        if id_i in mandatory_ids:
            add_linear(id_i, W_MANDATORY)
            
        parsed_times = lec_i.get("parsed_time", [])
        total_duration_minutes = 0
        
        for pt in parsed_times:
            day = pt['day']
            if day in lectures_by_day:
                lectures_by_day[day].append(lec_i)
            
            # Duration Calculation
            total_duration_minutes += (pt['end'] - pt['start'])
            
            # 1st period penalty
            if pt['start'] <= 570:
                add_linear(id_i, W_FIRST_CLASS)
            # Lunch time penalty
            if max(pt['start'], 720) < min(pt['end'], 780):
                add_linear(id_i, W_LUNCH_OVERLAP)

        # Time/Credit Mismatch Penalty
        duration_hours = total_duration_minutes / 60.0
        if duration_hours > c_i:
            add_linear(id_i, W_TIME_CREDIT_RATIO * (duration_hours - c_i))

    # -------------------------------------------------------------------------
    # 2. Quadratic Biases (Target Credits - Global pairs)
    # -------------------------------------------------------------------------
    # Note: Target credit cross-terms apply to ALL pairs. This is still O(N^2).
    # To optimize this further if N=4000, we might need to skip extremely low impact pairs,
    # but for now let's focus on the most expensive parts (overlaps/gaps).
    if progress_callback:
        progress_callback("Calculating credit interaction terms...", 30)

    for i in range(N):
        id_i = lectures[i]["id"]
        c_i = lectures[i]["credit"]
        for j in range(i + 1, N):
            id_j = lectures[j]["id"]
            c_j = lectures[j]["credit"]

            if id_i == id_j:
                continue
                
            add_quadratic(id_i, id_j, W_TARGET_CREDIT * (2 * c_i * c_j))

    # -------------------------------------------------------------------------
    # 3. Hard Constraints & Tension Model (Optimized by Day Grouping)
    # -------------------------------------------------------------------------
    if progress_callback:
        progress_callback("Checking time overlaps and tension models...", 60)

    days = ['월', '화', '수', '목', '금', '토', '일']
    for day_idx, d in enumerate(days):
        day_lectures = lectures_by_day[d]
        num_day_lecs = len(day_lectures)
        
        # Free Day Auxiliary Logic
        y_d = f"free_{d}"
        if num_day_lecs > 0: # Only bother if classes exist on this day
            add_linear(y_d, -R_FREE_DAY)
        
        for i in range(num_day_lecs):
            lec_i = day_lectures[i]
            id_i = lec_i['id']
            
            # Link to free day variable
            add_quadratic(id_i, y_d, P_FREE_DAY_BREAK)
            
            # Day-specific quadratic interactions
            for j in range(i + 1, num_day_lecs):
                lec_j = day_lectures[j]
                id_j = lec_j['id']
                
                # IMPORTANT: dimod does not allow self-interactions (u == v).
                # If a lecture has multiple periods on the same day, skip comparing it with itself.
                if id_i == id_j:
                    continue
                
                # check_overlap and calculate_time_gap are faster here
                if check_overlap(lec_i["parsed_time"], lec_j["parsed_time"]):
                    add_quadratic(id_i, id_j, W_HARD_OVERLAP)
                else:
                    gap = calculate_time_gap(lec_i["parsed_time"], lec_j["parsed_time"])
                    if 0 < gap <= 60:
                        add_quadratic(id_i, id_j, W_CONTIGUOUS_REWARD)
                    elif 60 < gap <= 180:
                        penalty = W_TENSION_BASE * math.sqrt(gap)
                        add_quadratic(id_i, id_j, penalty)
        
        if progress_callback:
            progress_callback(f"Analyzing day {d} ({day_idx+1}/7)...", 60 + int((day_idx+1)/7 * 30))

    if progress_callback:
        progress_callback("Finalizing BQM...", 95)

    # Apply all accumulated biases
    for var, bias in linear_biases.items():
        bqm.add_variable(var, bias)
        
    for (u, v), bias in quadratic_biases.items():
        bqm.add_interaction(u, v, bias)
                    
    return bqm

