"""
본 프로젝트는 2026학년도 1학기 개설강좌 데이터(약 4,400여 건)를 활용하여, 양자 컴퓨터가 해를 찾을 수 있도록 수치화된 행렬(Matrix)을 구축하는 전처리 단계를 수행했습니다.
한글 인코딩 오류와 불필요한 메타데이터를 정제하여 데이터의 신뢰성을 확보했으며, 특히 복잡한 형태의 시간표 텍스트(예: "화 16:30(75)")를 정규표현식으로 분석해 요일, 시작 시각, 수업 지속 시간을 숫자로 변환하는 로직을 구현했습니다.
이를 바탕으로 양자 어닐링의 목적 함수와 제약 조건을 구성할 핵심 행렬들을 생성했습니다. 각 강의의 학점 정보를 담은 '학점 벡터', 강의 간의 시간 중복 여부를 0과 1로 나타낸 '충돌 행렬', 그리고 모든 강의를 요일별로 분류한 '요일 배정 행렬'을 구축했습니다. 또한, 특정 시간대 선호도를 반영하기 위해 9시 시작 여부를 판별하는 행렬까지 생성을 완료했습니다.

"""


import pandas as pd
import numpy as np
from google.colab import drive

# 1. 출력 제한 해제 (터미널/주피터에서 모든 행과 열을 다 보여주게 설정)
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

# Google Drive 마운트 (파일이 Google Drive에 있는 경우 필수)
drive.mount('/content/drive', force_remount=True)

# 파일 경로를 올바른 Excel 파일 경로로 수정
file_path = '/content/drive/MyDrive/2. 2026학년도 1학기 학부 개설강좌 일람표(26.1.28.기준).xlsx'

# 2. 데이터 로드 (Excel 파일이므로 pd.read_excel 사용)
try:
    df = pd.read_excel(file_path, skiprows=6)
except Exception as e:
    print(f"❌ 파일 로드 중 오류가 발생했습니다: {e}")
    # 오류 발생 시 이후 코드 실행을 방지하기 위해 여기서 종료
    raise

# 3. 전처리: 컬럼명 공백 제거 및 필요 데이터만 추출
df.columns = df.columns.str.strip()
# 연번, 교과목명, 학점, 시간표만 가져오기
clean_df = df[['연번', '교과목명', '학점', '시간표']].dropna(subset=['연번'])

# 4. 데이터 타입 변환
clean_df['연번'] = clean_df['연번'].astype(int)
clean_df['학점'] = pd.to_numeric(clean_df['학점'], errors='coerce').fillna(0).astype(int)

# ---------------------------------------------------------
# [A] 연번-학점 매핑 행렬 (1차원 벡터)
# 모든 과목의 학점을 연번 순서대로 나열한 행렬입니다.
credits_matrix = clean_df['학점'].values

# [B] 연번-시간표 매핑 리스트
# 시간 겹침(Conflict Matrix)을 계산하기 위한 기초 데이터입니다.
schedule_list = clean_df['시간표'].fillna("미지정").values

# 5. 결과 출력 (모든 행렬값 출력)
print("=== [모든 학점 행렬값 (Total: {})] ===".format(len(credits_matrix)))
print(credits_matrix)

print("\n=== [모든 연번-학점 매핑 데이터] ===")
# 전체 데이터를 리스트 형태의 행렬로 보고 싶을 때
full_matrix_data = clean_df[['연번', '학점']].values
print(full_matrix_data)


# 6. 파일로 저장 (행렬값이 너무 많아 화면에서 보기 힘들 때 사용)
# np.savetxt('credits_matrix.csv', credits_matrix, delimiter=',')
# print("\n✅ 'credits_matrix.csv' 파일로 모든 행렬값이 저장되었습니다.")

import pandas as pd
import numpy as np
import re
from google.colab import drive

# Google Drive 마운트 (파일이 Google Drive에 있는 경우 필수)
drive.mount('/content/drive', force_remount=True)

# 1. 데이터 로드 및 전처리
# 파일 경로를 올바른 Excel 파일 경로로 수정
file_path = '/content/drive/MyDrive/2. 2026학년도 1학기 학부 개설강좌 일람표(26.1.28.기준).xlsx'

try:
    # Excel 파일이므로 pd.read_excel 사용
    df = pd.read_excel(file_path, skiprows=6)
except Exception as e:
    print(f"❌ 파일 로드 중 오류가 발생했습니다: {e}")
    # 오류 발생 시 이후 코드 실행을 방지하기 위해 여기서 종료
    raise

df.columns = df.columns.str.strip()
# 시간표 정보가 있는 상위 50개 과목으로 먼저 테스트 (전체로 확대 가능)
sample_df = df.dropna(subset=['연번', '시간표']).head(50).copy()
sample_df['연번'] = sample_df['연번'].astype(int)

# 2. 시간표 파싱 함수: "화 16:30(75)" -> {'day': '화', 'start': 990, 'end': 1065}
def parse_time_to_range(sched_str):
    if pd.isna(sched_str): return []
    # 패턴: 요일(월-일), 시간(00:00), 기간(숫자)
    pattern = r'([월화수목금토일])\s*(\d{2}):(\d{2})\((\d+)\)'
    matches = re.findall(pattern, str(sched_str))

    intervals = []
    for day, hr, mn, dur in matches:
        start_min = int(hr) * 60 + int(mn) # 하루 시작 기준 분(minute) 계산
        end_min = start_min + int(dur)
        intervals.append({'day': day, 'start': start_min, 'end': end_min})
    return intervals

# 3. 겹침 판정 함수: 하나라도 겹치는 시간이 있으면 True
def check_overlap(list1, list2):
    for time1 in list1:
        for time2 in list2:
            # 같은 요일이고 시간이 교차하는지 확인
            if time1['day'] == time2['day']:
                if max(time1['start'], time2['start']) < min(time1['end'], time2['end']):
                    return True
    return False

# 4. 행렬 생성 (Overlap Matrix)
n = len(sample_df)
overlap_matrix = np.zeros((n, n), dtype=int)
schedules = sample_df['시간표'].apply(parse_time_to_range).tolist()

for i in range(n):
    for j in range(i + 1, n):
        if check_overlap(schedules[i], schedules[j]):
            overlap_matrix[i, j] = 1
            overlap_matrix[j, i] = 1 # 대칭 행렬

# 5. 결과 시각화 (Pandas DataFrame으로 가독성 높게 표시)
overlap_df = pd.DataFrame(overlap_matrix,
                          index=sample_df['연번'],
                          columns=sample_df['연번'])

print("=== Overlap Matrix (행/열은 강의 연번) ===")
print(overlap_df.iloc[:10, :10]) # 상위 10x10만 출력

# 파일로 저장하여 전체 확인
# overlap_df.to_csv('overlap_matrix.csv')

import pandas as pd
import numpy as np
import re
from google.colab import drive

# Google Drive 마운트 (파일이 Google Drive에 있는 경우 필수)
drive.mount('/content/drive', force_remount=True)

# 1. 데이터 로드 (에러 방지용 인코딩 설정)
# 파일 경로를 올바른 Excel 파일 경로로 수정
file_path = '/content/drive/MyDrive/2. 2026학년도 1학기 학부 개설강좌 일람표(26.1.28.기준).xlsx'

try:
    # Excel 파일이므로 pd.read_excel 사용
    df = pd.read_excel(file_path, skiprows=6)
except Exception as e:
    print(f"❌ 파일 로드 중 오류가 발생했습니다: {e}")
    # 오류 발생 시 이후 코드 실행을 방지하기 위해 여기서 종료
    raise

# 2. 전처리: 컬럼명 공백 제거 및 필요 데이터(연번, 시간표)만 추출
df.columns = df.columns.str.strip()
df = df.dropna(subset=['연번', '시간표'])
df['연번'] = df['연번'].astype(int)

# 3. 요일별 연번 분류 리스트 생성
days_of_week = ['월', '화', '수', '목', '금', '토', '일']
day_to_ids = {day: [] for day in days_of_week}

for _, row in df.iterrows():
    lecture_id = row['연번']
    schedule_str = str(row['시간표'])

    # 시간표 문자열에서 요일(월~일) 글자 추출
    found_days = re.findall(r'[월화수목금토일]', schedule_str)
    for d in set(found_days): # 한 과목이 같은 요일에 여러 번 있어도 한 번만 체크
        day_to_ids[d].append(lecture_id)

# 4. [핵심] 분류된 데이터를 바탕으로 Matrix(행렬) 생성
# 모든 고유 연번을 행으로 정의
all_lecture_ids = sorted(df['연번'].unique())
# (강의 수 x 7개 요일) 크기의 영행렬 생성
membership_matrix = np.zeros((len(all_lecture_ids), len(days_of_week)), dtype=int)

# 연번을 행 인덱스로 매핑
id_to_row_idx = {lid: i for i, lid in enumerate(all_lecture_ids)}

# 각 요일 리스트를 순회하며 행렬에 1을 채움
for col_idx, day in enumerate(days_of_week):
    for lid in day_to_ids[day]:
        row_idx = id_to_row_idx[lid]
        membership_matrix[row_idx, col_idx] = 1

# 5. 시각적 확인을 위해 DataFrame으로 변환
matrix_df = pd.DataFrame(membership_matrix, index=all_lecture_ids, columns=days_of_week)

# 결과 출력
print("=== 요일별 강의 연번 분류 (상위 5개씩) ===")
for day in days_of_week:
    print(f"{day}요일: {day_to_ids[day][:5]}...")

print("\n=== 최종 요일 배정 행렬 (Matrix) ===")
print(matrix_df.head(15)) # 상위 15개 연번의 행렬값 출력

import pandas as pd
import numpy as np
from google.colab import drive

# Google Drive 마운트 (파일이 Google Drive에 있는 경우 필수)
drive.mount('/content/drive', force_remount=True)

# 1. 고속 데이터 로드
# 파일 경로를 올바른 Excel 파일 경로로 수정하고, pd.read_excel 사용
file_path = '/content/drive/MyDrive/2. 2026학년도 1학기 학부 개설강좌 일람표(26.1.28.기준).xlsx'

# 9시 여부 판별에 필요한 '연번'과 '시간표' 컬럼만 로드
# Excel 파일의 경우 usecols 인덱싱이 다를 수 있으므로 컬럼명으로 지정
cols_to_use = ['연번', '시간표']

try:
    # Excel 파일이므로 pd.read_excel 사용
    df = pd.read_excel(file_path, skiprows=6, usecols=cols_to_use)
except Exception as e:
    print(f"❌ 파일 로드 중 오류가 발생했습니다: {e}")
    # 오류 발생 시 이후 코드 실행을 방지하기 위해 여기서 종료
    raise

# 2. 전처리 (결측치 제거 및 정렬)
df = df.dropna(subset=['연번'])
df['연번'] = df['연번'].astype(int)
df = df.sort_values(by='연번') # 연번 순서대로 정렬
df['시간표'] = df['시간표'].fillna('') # 시간표가 NaN인 경우 빈 문자열로 처리

# 3. '09:00' 포함 여부 판별 (Vectorized Operation)
# 시간표 텍스트에 '09:00'이 있으면 1, 없으면 0
df['is_9am'] = df['시간표'].str.contains('09:00', na=False).astype(int)

# 4. 최종 행렬(Matrix) 생성
# 양자 어닐링 모델의 입력값으로 바로 사용할 수 있는 Numpy array 형태
nine_am_matrix = df['is_9am'].values.reshape(-1, 1)

# 5. 행렬식 출력 (Matrix Format)
print(f"📊 Matrix Shape: {nine_am_matrix.shape} (Rows x Columns)")
print("\n=== 9 AM Start Matrix (Column Vector) ===\n")
print(nine_am_matrix) # Numpy의 기본 출력 형식을 사용하여 행렬 형태로 보여줌

# 6. 특정 연번 확인 (검증)
# 예: 연번 8번의 인덱스 위치 확인
# df는 연번으로 정렬되어 있으므로, 8번 연번의 위치를 찾아야 함
target_연번 = 8
if target_연번 in df['연번'].values:
    sample_idx = df[df['연번'] == target_연번].index[0]
    print(f"\n💡 [Check] Index {sample_idx} (연번 {df.loc[sample_idx]['연번']}) value: {nine_am_matrix[sample_idx][0]}")
else:
    print(f"\n💡 [Check] 연번 {target_연번}번을 찾을 수 없습니다.")