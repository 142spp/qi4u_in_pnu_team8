# 🎓 양자 컴퓨팅 기반 시간표 최적화 웹 서비스 (팀 8)

약 200개의 대학교 개설 강의 중 학생의 선호도와 필수 제약 조건을 반영하여 최적의 시간표를 도출하는 웹 서비스입니다.

## 🚀 프로젝트 개요
이 프로젝트는 복잡한 시간표 구성 문제를 해결하기 위해 양자 어닐링(Quantum Annealing)을 모방한 **Simulated Annealing 알고리즘**을 활용한 **QUBO (Quadratic Unconstrained Binary Optimization)** 모델링을 수행하여 스케줄링을 진행합니다.

## 🛠 기술 스택
### Frontend
- **Framework:** Next.js (App Router)
- **Styling:** Tailwind CSS, shadcn/ui
- **State Management:** Zustand (Client State), TanStack Query (Server State & 비동기 UI 처리)

### Backend
- **Framework:** Python FastAPI
- **Algorithm:** dimod (Simulated Annealing 기반 접근법 도입)
- **Async Task Queue:** FastAPI BackgroundTasks (In-Memory Processing)
- **Database & ORM:** None (In-Memory Data Storage using Python Dicts/Pandas)

### Infrastructure
- **Containerization:** Docker, Docker Compose

## 💡 주요 아키텍처 및 특징

### 1. 비동기 백엔드 구조 및 상태 폴링
- 양자 최적화 계산 시 FastAPI 메인 스레드를 블로킹하지 않도록 `BackgroundTasks` 방식으로 비동기 위임합니다.
- 클라이언트는 `/api/optimize` 호출 후 발급받은 `task_id`를 기반으로 1초 간격으로 상태를 폴링(Polling)하여 현재 연산 상태(PENDING, PROCESSING, SUCCESS, FAILURE)를 확인하도록 구현되었습니다.
- 결과 수신 시 프론트엔드 스토어에 즉각 반영되도록 구성되어 있습니다.

### 2. 최적화 제약조건 (QUBO 모델링)
- **Hard Constraints (필수 조건):** 시간대 중복 방지, 필수 과목 누락 방지 등.
- **Soft Constraints (소프트 조건):** 사용자의 학점(Credit) 선호도, 연강 선호 및 공강 확보 조건 등을 반영하도록 페널티 가중치(Weights) 구성의 기반이 마련됩니다.

### 3. 직관적인 사용자 경험(UX) 최적화
- **성능 고려 레이아웃:** 4,000여 개의 대규모 리스트 필터링 시 성능 최적화를 위해 **300ms 디바운싱(Debounce)** 처리와 표시 갯수 제한(가상화 우회)을 두었습니다.
- **레이아웃 및 테마 편의성:** 좌측엔 검색 및 목표학점 입력 패널, 우측엔 넓은 절대좌표 기반(Absolute Positioning) 블록형 시간표로 기능을 분리, 살구/피치톤(`FDC3A1`) 원포인트 컬러 전략으로 시각적 피로도를 낮췄습니다.
- **정규식 기반 시간 파서:** `수 13:30-15:30` 또는 `금 09:00(50)(외부)` 등 복잡한 학사 시간 포맷 문자열을 파싱하는 `timeParser.ts`가 자체 내장되어 다양한 강의 형식을 지원합니다.

## ⚙️ 실행 방법 (Running the Service)

프론트엔드, 백엔드는 각각 독립된 Docker 컨테이너로 실행될 수 있도록 구성되어 있습니다.

```bash
# 전체 서비스 (Frontend + Backend) 컨테이너 실행
docker-compose up --build
```

- **Frontend:** `http://localhost:3000` 에서 접속 가능
- **Backend API (Swagger UI):** `http://localhost:8000/docs` 에서 엔드포인트 테스트 가능
