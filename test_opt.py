import json
import urllib.request
import urllib.error
import time
import sys

URL = "http://localhost:8000/optimize"
headers = {'Content-Type': 'application/json'}

try:
    print("Fetching all lectures to find valid IDs...")
    req = urllib.request.Request("http://localhost:8000/lectures")
    with urllib.request.urlopen(req) as response:
        lectures_data = json.loads(response.read().decode())
    lectures = lectures_data.get("lectures", [])
    valid_ids = [lec["id"] for lec in lectures][:20]
    
    if not valid_ids:
        print("No lectures found.")
        sys.exit(1)
        
    print(f"Using valid IDs: {valid_ids}")
    
    payload = {
        "selected_lecture_ids": valid_ids,
        "target_credits": 21.0,
        "prefer_contiguous": True,
        "prefer_free_days": False
    }

    print("Submitting optimization task...")
    req = urllib.request.Request(URL, data=json.dumps(payload).encode(), headers=headers)
    with urllib.request.urlopen(req) as response:
        res_data = json.loads(response.read().decode())
    
    print("Response:", res_data)
    task_id = res_data.get('task_id')
    
    if task_id:
        print(f"Task ID: {task_id}")
        for i in range(20):
            req = urllib.request.Request(f"http://localhost:8000/optimize/{task_id}")
            with urllib.request.urlopen(req) as response:
                status_data = json.loads(response.read().decode())
            
            print(f"Status check {i+1}:", status_data["status"])
            if status_data.get("status") in ["SUCCESS", "FAILURE"]:
                print("Final result:", status_data)
                break
            time.sleep(1)
except Exception as e:
    print("Error:", e)
