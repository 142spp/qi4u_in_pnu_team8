# ==========================================
# [셀 1] 필수 라이브러리 설치 및 전처리 (정규식 업그레이드)
# ==========================================
!pip install pyqubo dwave-neal tqdm

import pandas as pd
import numpy as np
import re
from google.colab import drive
from tqdm import tqdm

pd.set_option('display.max_rows', None)
drive.mount('/content/drive', force_remount=True)

file_path = '/content/drive/MyDrive/2. 2026학년도 1학기 학부 개설강좌 일람표(26.1.28.기준).xlsx'
df = pd.read_excel(file_path, skiprows=6)
df.columns = df.columns.str.strip()

clean_df = df[['연번', '교과목명', '학점', '시간표']].dropna(subset=['연번', '시간표']).copy()
clean_df['연번'] = clean_df['연번'].astype(int)
clean_df['학점'] = pd.to_numeric(clean_df['학점'], errors='coerce').fillna(0).astype(int)

course_ids = clean_df['연번'].tolist()
credits_dict = dict(zip(clean_df['연번'], clean_df['학점']))
course_name_dict = dict(zip(clean_df['연번'], clean_df['교과목명']))
sched_str_dict = dict(zip(clean_df['연번'], clean_df['시간표']))

# 💡 하이픈(-) 방식과 괄호() 방식의 시간표를 모두 읽을 수 있도록 파싱 함수 강화!
def parse_time_to_range(sched_str):
    if pd.isna(sched_str): return []
    intervals = []
    
    # 1. 괄호 방식: 화 16:30(75) 507-102
    pattern1 = r'([월화수목금토일])\s*(\d{2}):(\d{2})\((\d+)\)(?:\s*([가-힣A-Za-z0-9-]+))?'
    for day, hr, mn, dur, room in re.findall(pattern1, str(sched_str)):
        start_min = int(hr) * 60 + int(mn) 
        intervals.append({'day': day, 'start': start_min, 'end': start_min + int(dur), 'room': room.strip() if room else '알수없음'})
        
    # 2. 하이픈 방식: 수 13:30-16:30 밀양M03-3350
    pattern2 = r'([월화수목금토일])\s*(\d{2}):(\d{2})-(\d{2}):(\d{2})(?:\s*([가-힣A-Za-z0-9-]+))?'
    for day, shr, smn, ehr, emn, room in re.findall(pattern2, str(sched_str)):
        start_min = int(shr) * 60 + int(smn)
        end_min = int(ehr) * 60 + int(emn)
        intervals.append({'day': day, 'start': start_min, 'end': end_min, 'room': room.strip() if room else '알수없음'})
        
    return intervals

def check_overlap(list1, list2):
    for time1 in list1:
        for time2 in list2:
            if time1['day'] == time2['day']:
                if max(time1['start'], time2['start']) < min(time1['end'], time2['end']): return True
    return False

def calculate_distance(room1, room2):
    if room1 == '알수없음' or room2 == '알수없음': return 500
    if ('양산' in room1) != ('양산' in room2) or ('밀양' in room1) != ('밀양' in room2): return 50000  
    m1, m2 = re.search(r'(\d+)-', room1), re.search(r'(\d+)-', room2)
    if m1 and m2:
        b1, b2 = int(m1.group(1)), int(m2.group(1))
        if b1 == b2: return 0 
        z_diff = abs(b1 // 100 - b2 // 100)
        return 100 if z_diff == 0 else z_diff * 300           
    return 500 

n = len(clean_df)
schedules = clean_df['시간표'].apply(parse_time_to_range).tolist()

print("⏳ 1/2: 시간 겹침 행렬 생성 중...")
overlap_pairs = set() 
for i in tqdm(range(n)):
    for j in range(i + 1, n):
        if check_overlap(schedules[i], schedules[j]):
            overlap_pairs.add((course_ids[i], course_ids[j]))

print("⏳ 2/2: 거리, 시간차, 점심시간 데이터 생성 중...")
lunch_start, lunch_end = 12 * 60, 13 * 60
lunch_courses = set() 
same_day_pairs = []
time_gap = {}
distance = {}

for i in tqdm(range(n)):
    id_i = course_ids[i]
    for t_i in schedules[i]:
        if max(t_i['start'], lunch_start) < min(t_i['end'], lunch_end):
            lunch_courses.add(id_i)

    for j in range(i + 1, n):
        id_j = course_ids[j]
        if (id_i, id_j) in overlap_pairs or (id_j, id_i) in overlap_pairs: continue 
            
        for t_i in schedules[i]:
            for t_j in schedules[j]:
                if t_i['day'] == t_j['day']:
                    if t_i['end'] <= t_j['start']: gap = t_j['start'] - t_i['end']
                    elif t_j['end'] <= t_i['start']: gap = t_i['start'] - t_j['end']
                    else: continue
                    pair = (id_i, id_j)
                    same_day_pairs.append(pair)
                    time_gap[pair] = gap
                    distance[pair] = calculate_distance(t_i['room'], t_j['room']) 

print("\n✅ 셀 1 전처리 완료! 이제 메모리에 데이터가 저장되었습니다. 셀 2로 넘어가세요.")
