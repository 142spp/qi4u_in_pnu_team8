import math
from ..utils.time_utils import check_overlap, calculate_time_gap

try:
    import dimod
except ImportError:
    pass

def build_timetable_bqm(lectures, preferences):
    """
    Builds the Binary Quadratic Model (BQM) for timetable optimization based on Hard and Soft constraints.
    """
    bqm = dimod.BinaryQuadraticModel('BINARY')
    
    # Extract preferences
    max_credits = preferences.get("max_credits", 21.0)
    mandatory_ids = preferences.get("mandatory_ids", [])
    
    N = len(lectures)
    
    # -------------------------------------------------------------------------
    # 0. Base Weights / Penalties Definitions
    # -------------------------------------------------------------------------
    W_HARD_OVERLAP = 10000.0
    W_TARGET_CREDIT = 10.0
    W_MANDATORY = -10000.0  # Encourage mandatory classes
    
    # Soft constraints - Linear
    W_FIRST_CLASS = 50.0   # Penalty for 1st period (e.g. 9:00 started classes)
    W_LUNCH_OVERLAP = 30.0 # Penalty for eating during 12:00-13:00
    
    # Soft constraints - Free Days
    R_FREE_DAY = 100.0     # Reward for having a free day
    P_FREE_DAY_BREAK = 500.0 # Penalty if a class is on a declared free day
    
    # Soft constraints - Tension Model
    W_CONTIGUOUS_REWARD = -20.0  # Reward for gap <= 60 minutes
    W_TENSION_BASE = 5.0         # Base penalty for tension (gap > 60 and gap <= 180)
    
    linear_biases = {}
    quadratic_biases = {}
    
    def add_linear(var, bias):
        linear_biases[var] = linear_biases.get(var, 0.0) + bias
        
    def add_quadratic(u, v, bias):
        # normalize order to prevent directed edges creating duplicated entries
        if str(u) > str(v): 
            u, v = v, u
        quadratic_biases[(u, v)] = quadratic_biases.get((u, v), 0.0) + bias

    # -------------------------------------------------------------------------
    # 1. Variables Definition & Linear Biases (Soft Constraints 1 & Mandatory)
    # -------------------------------------------------------------------------
    for i in range(N):
        lec_i = lectures[i]
        id_i = lec_i["id"]
        c_i = lec_i["credit"]
        
        # Target Credit Linear Term: A * (c_i^2 - 2 * K * c_i)
        add_linear(id_i, W_TARGET_CREDIT * (c_i**2 - 2 * max_credits * c_i))
        
        # Mandatory Requirement
        if id_i in mandatory_ids:
            add_linear(id_i, W_MANDATORY)
            
        # 1st Period & Lunch Time Penalty
        parsed_times = lec_i.get("parsed_time", [])
        for pt in parsed_times:
            # 1st period (starts before or equal to 9:30 AM = 9*60+30 = 570 minutes)
            if pt['start'] <= 570:
                add_linear(id_i, W_FIRST_CLASS)
            # Lunch time (12:00 - 13:00 => 720 - 780 minutes)
            if max(pt['start'], 720) < min(pt['end'], 780):
                add_linear(id_i, W_LUNCH_OVERLAP)

        # Target Credit Quadratic Term: A * (2 * c_i * c_j)
        for j in range(i + 1, N):
            id_j = lectures[j]["id"]
            c_j = lectures[j]["credit"]
            add_quadratic(id_i, id_j, W_TARGET_CREDIT * (2 * c_i * c_j))
            
    # -------------------------------------------------------------------------
    # 2. Hard Constraints (Time Overlap)
    # -------------------------------------------------------------------------
    for i in range(N):
        for j in range(i + 1, N):
            if check_overlap(lectures[i]["parsed_time"], lectures[j]["parsed_time"]):
                add_quadratic(lectures[i]["id"], lectures[j]["id"], W_HARD_OVERLAP)

    # -------------------------------------------------------------------------
    # 3. Soft Constraints 2: Free Days (Auxiliary Variables)
    # -------------------------------------------------------------------------
    days = ['월', '화', '수', '목', '금']
    for d in days:
        y_d = f"free_{d}"
        add_linear(y_d, -R_FREE_DAY) # Base reward for claiming free day
        
        for i in range(N):
            id_i = lectures[i]['id']
            on_day_d = any(pt['day'] == d for pt in lectures[i].get('parsed_time', []))
            if on_day_d:
                # Strong penalty if class is on 'claimed' free day
                add_quadratic(id_i, y_d, P_FREE_DAY_BREAK)

    # -------------------------------------------------------------------------
    # 4. Soft Constraints 3: Tension Model (Quadratic Biases)
    # -------------------------------------------------------------------------
    for i in range(N):
        for j in range(i + 1, N):
            gap = calculate_time_gap(lectures[i]["parsed_time"], lectures[j]["parsed_time"])
            if gap > 0:
                if gap <= 60:
                    # Clustering reward for contiguous classes
                    add_quadratic(lectures[i]["id"], lectures[j]["id"], W_CONTIGUOUS_REWARD)
                elif gap <= 180:
                    # Tension penalty for awkward gaps using sqrt to prevent runaway explosion
                    penalty = W_TENSION_BASE * math.sqrt(gap)
                    add_quadratic(lectures[i]["id"], lectures[j]["id"], penalty)
                else:
                    # gap > 180: Counted as separate groups, 0 quadratic interaction
                    pass

    # Apply all accumulated biases
    for var, bias in linear_biases.items():
        bqm.add_variable(var, bias)
        
    for (u, v), bias in quadratic_biases.items():
        bqm.add_interaction(u, v, bias)
                    
    return bqm
