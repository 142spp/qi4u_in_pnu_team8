---
trigger: manual
---

# 📌 Project Progress (Session Checkpoint)

현재까지 진행된 양자 컴퓨팅 기반 시간표 최적화 웹 서비스(프로토타입)의 상태와 향후 개발되어야 할 남은 작업들을 정리한 문서입니다.

## ✅ 현재까지 달성한 작업 (Completed)

### 1. 프로젝트 아키텍처 및 요구사항 재설계
- 1일 프로토타입 완성을 위해 **In-Memory 아키텍처**로 프로젝트 설계 전면 단순화.
- 무거운 인프라(PostgreSQL, Redis, Celery) 제거 및 로컬 기반 환경 구축 완성.
- 백엔드(FastAPI)와 프론트엔드(Next.js) 코어 폴더 구조 세팅 완료.

### 2. 알고리즘 모델링 연동 (Backend)
- D-Wave 실제 하드웨어의 점검 이슈 대응을 위해 `dimod`의 **Simulated Annealing** 모델로 교체.
- Pandas를 활용한 서버 구동 시 `lectures.csv` 데이터 로드 및 전역 메모리 적재 로직 구현.
- `FastAPI BackgroundTasks`를 활용한 비동기 백그라운드 모델 연산 라우터(`/api/optimize`) 작업 완성.

### 3. 클라이언트 UI 구성 (Frontend)
- Next.js App Router + Tailwind CSS 기반 환경 세팅 및 `shadcn/ui` 컴포넌트 이식 완료 (Button, Card, Checkbox, Progress 등).
- **Zustand**를 사용한 전역 상태 관리 저장소 구성 (강의 선택 등 UI 상태).
- **TanStack Query**를 이용하여 백엔드의 연산 상태(`Pending -> Processing -> Success`)를 실시간으로 `1초`마다 Polling하는 프로그레스 바 렌더링 구현.
- `LectureList` 컴포넌트, `OptimizationPanel` 및 결과 확인용 `TimetableView` 컴포넌트 프레임워크 구축 완료.

### 4. 인프라 연동
- FastAPI와 Next.js 서버를 동시에 컨테이너로 띄울 수 있도록 `Dockerfile` 및 `docker-compose.yml` 스크립트 작성 완료.

---

## 🚀 앞으로 해야 할 일 (To-Do / Next Steps)

### 1. 알고리즘 모델 정교화 (QUBO 고도화)
- [ ] **Soft Constraint 로직 구현**: 현재 구성된 시간 중복 방지(Hard Constraint) 외에, **연강 선호도**, **공강 확보(특정 요일 휴식)** 등 유저의 선호도를 페널티/리워드로 수식화하여 BQM 파이프라인에 추가해야 합니다.
- [ ] 데이터 파싱 로직 구체화: 현재의 하드 코딩 된 시간/요약(문자열 매칭) 겹침 방지 로직을, 실제 시간표 블록 인덱스(ex: 월요일 1교시 = 0) 단위로 쪼개어 연산하도록 `quantum_optimizer.py`의 파싱 로직을 구현해야 합니다.

### 2. 백엔드/프론트엔드 데이터 통신 안정화
- [ ] 강의 필터링 기능 추가: 전공/교양, 학점 단위, 교수명 등으로 클라이언트에서 손쉽게 강의를 필터링 할 수 있는 검색바 컴포넌트 구현.
- [ ] 시간표 시각화(Grid) 개선: 현재 목록형으로 단순히 나열되는 최적화 결과를, HTML Table이나 CSS Grid를 사용해 실제 에브리타임(Everytime)과 같은 주간 시간표 형태로 렌더링하는 UI 개선.

### 3. 예외 처리 및 환경 안정화
- [ ] 예외 처리 세분화: 최적화 가능한 강의 조합을 찾지 못했을 경우(Energy Level 등) 프론트엔드에 명확한 사유를 전달하는 에러 핸들링.
- [ ] Docker WSL 환경 종속성 트러블슈팅 및 Production 급의 배포 환경(테스트 등) 준비.
