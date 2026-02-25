import pandas as pd
import re


# Load CSV
df = pd.read_csv("lectures.csv", encoding="euc-kr")


# Prevent float error
df["시간표"] = df["시간표"].fillna("").astype(str)




# Function to extract everything
def parse_timetable(timetable):


    # Split sessions
    sessions = [s.strip() for s in timetable.split(',') if s.strip()]
   
    days = []
    first_time = None
    first_building = None
    first_room = None
   
    for i, session in enumerate(sessions):
       
        # Extract day
        day_match = re.match(r'([월화수목금토일])', session)
        if day_match:
            days.append(day_match.group(1))
       
        # Extract first time/building/room only
        if i == 0:
           
            time_match = re.search(r'(\d{2}:\d{2})', session)
            if time_match:
                first_time = time_match.group(1)
           
            location_match = re.search(r'(\d+)-(\d+)', session)
            if location_match:
                first_building = location_match.group(1)
                first_room = location_match.group(2)
   
    return pd.Series([days, first_time, first_building, first_room])




df[["요일", "시작시간", "강의동", "강의실"]] = df["시간표"].apply(parse_timetable)




# Result check
#print(df[["교과목명", "요일", "시작시간", "강의동", "강의실"]].head())


courses = df[[
    "연번",
    "교과목번호",
    "분반",
    "교과목명",
    "학점",
    "요일",
    "시작시간",
    "강의동",
    "강의실"
]].copy()


print(courses)


import numpy as np
import pandas as pd




# ============================
# HELPER FUNCTIONS
# ============================


def time_overlap(course_i, course_j):
    """
    Check if two courses overlap in time on same day
    """


    common_days = set(course_i['day_num']) & set(course_j['day_num'])


    if not common_days:
        return False


    start_i = course_i['time_min']
    end_i = start_i + course_i['duration_min']


    start_j = course_j['time_min']
    end_j = start_j + course_j['duration_min']


    return not (end_i <= start_j or end_j <= start_i)




def time_gap(course_i, course_j):
    """
    Compute gap between two courses (minutes)
    """


    if set(course_i['day_num']) & set(course_j['day_num']):


        end_i = course_i['time_min'] + course_i['duration_min']
        start_j = course_j['time_min']


        gap = start_j - end_i


        if gap > 0:
            return gap


    return None




# ============================
# QUBO BUILDER
# ============================


def build_qubo(df, K, distance_matrix,
               A=10, B=100, C=200, D=1):


    courses = df.to_dict("records")


    N = len(courses)


    Q = np.zeros((N,N))




    # ------------------------
    # CREDIT TERM (A)
    # ------------------------


    for i in range(N):


        ci = courses[i]['credit']


        Q[i,i] += A * (ci**2 - 2*K*ci)


        for j in range(i+1, N):


            cj = courses[j]['credit']


            Q[i,j] += A * (2 * ci * cj)
            Q[j,i] = Q[i,j]




    # ------------------------
    # MANDATORY TERM (B)
    # ------------------------


    for i in range(N):


        if courses[i]['mandatory'] == 1:


            Q[i,i] += -B




    # ------------------------
    # OVERLAP TERM (C)
    # ------------------------


    for i in range(N):


        for j in range(i+1, N):


            if time_overlap(courses[i], courses[j]):


                Q[i,j] += C
                Q[j,i] = Q[i,j]




    # ------------------------
    # WALKING TERM (D)
    # ------------------------


    for i in range(N):


        for j in range(i+1, N):


            gap = time_gap(courses[i], courses[j])


            if gap is not None and gap > 0:


                b1 = courses[i]['building_id']
                b2 = courses[j]['building_id']


                dist = distance_matrix[b1][b2]


                penalty = D * (dist / gap)


                Q[i,j] += penalty
                Q[j,i] = Q[i,j]




    return Q


print(build_qubo(courses, K, distance_matrix,
               A=10, B=100, C=200, D=1))


K = target credits
























Data Extraction from CSV File
2.1 Source Data
The lecture dataset was provided in CSV format. The file contains information about courses, including:
Course ID (교과목번호)


Course name (교과목명)


Credit value (학점)


Timetable information (시간표)


Lecture building and room


Other metadata
The timetable information is separated as following:
Lecture day (a list)


Start time


Duration


Building number


Room number
Final Processed Dataset Format
Each course is represented as a structured record extracting the desired columns. 

