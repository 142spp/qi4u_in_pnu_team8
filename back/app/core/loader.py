import pandas as pd
import pathlib

# In-memory storage for lectures
global_lectures_store = []

def load_lectures():
    global global_lectures_store
    data_path = pathlib.Path(__file__).parent.parent.parent / "data" / "lectures.csv"
    
    if not data_path.exists():
        print(f"Warning: Data file not found at {data_path}")
        return

    # Read CSV
    df = pd.read_csv(data_path)
    
    # Fill NaN
    df = df.fillna("")

    # Process to list of dicts for easy access
    global_lectures_store.clear()
    seen_ids = set()
    for _, row in df.iterrows():
        lec_id = str(row["교과목번호"]) + "-" + str(row["분반"])
        if lec_id in seen_ids:
            continue
            
        time_room_val = str(row["시간표"]).strip()
        if not time_room_val:
            continue
            
        seen_ids.add(lec_id)
        
        global_lectures_store.append({
            "id": lec_id,
            "number": str(row["교과목번호"]),
            "class_num": str(row["분반"]),
            "name": str(row["교과목명"]),
            "credit": float(row["학점"]) if row["학점"] else 0.0,
            "time_room": time_room_val,
            "professor": str(row["교수명"]),
            "category": str(row["교과목구분"])
        })
    print(f"Loaded {len(global_lectures_store)} lectures.")

def get_all_lectures():
    return global_lectures_store

def get_lecture_by_id(lec_id: str):
    for lec in global_lectures_store:
        if lec["id"] == lec_id:
            return lec
    return None
