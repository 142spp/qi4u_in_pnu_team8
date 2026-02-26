# 시간표 최적화 양자 어닐링(Simulated Annealing) 모델 요약

본 프로젝트는 시간표 작성 문제를 **QUBO (Quadratic Unconstrained Binary Optimization)** 모델로 정식화하고, **Simulated Annealing** (MCMC 기반의 휴리스틱 탐색 알고리즘)을 통해 최적의 시간표 조합을 탐색합니다. `dimod` 및 `neal` 라이브러리를 사용하여 파이썬 환경에서 BQM(Binary Quadratic Model)을 구성하고 해를 도출합니다.

## 1. 변수 정의 (Variables)

최적화 대상이 되는 이진 변수(Binary Variable)는 두 종류로 구성됩니다.

*   $x_i \in \{0, 1\}$: 과목 $i$의 선택 여부 (1: 선택, 0: 미선택)
*   $y_d \in \{0, 1\}$: 요일 $d$의 공강(Free day) 여부 (1: 해당 요일 공강, 0: 수업 있음)

## 2. 목적 함수 (Objective Function) 상세

본 시간표 최적화 모델의 최종 목적 함수(에너지 $E$)는 여러 고려 변수들의 합으로 구성됩니다.
다음과 같이 전체 에너지를 각 제약 조건의 선형 결합으로 표현합니다.

$$E = E_{\text{target}} + E_{\text{mandatory}} + E_{\text{overlap}} + E_{\text{tension}} + E_{\text{contig}} + E_{\text{soft}} + E_{\text{free}}$$

에너지 값이 낮을수록 (Energy Minimum) 최적의 시간표로 간주됩니다. 여기서 $x_i, x_j, y_d \in \{0, 1\}$ 입니다.

### 2.1 주요 에너지 항 (Main Energy Terms)

첨부해주신 수식 형태에 맞춰 우리 프로젝트의 제약 조건들을 수학적으로 공식화하면 다음과 같습니다.

*   **목표 학점 달성 ($E_{\text{target}}$):**
    사용자가 원하는 목표 학점 $T$에 도달하도록 유도합니다. $c_i$는 과목 $i$의 학점입니다.
    $$E_{\text{target}} = \lambda_{\text{credit}} \left(\sum_i c_i x_i - T\right)^2$$

*   **필수 수강 과목 ($E_{\text{mandatory}}$):**
    사용자가 직접 선택한 필수 과목 집합 $M$에 포함된 과목은 반드시 들어야 합니다. (선택 안 하면 페널티 부과)
    $$E_{\text{mandatory}} = \lambda_{\text{man}} \sum_{i \in M} (1 - x_i)$$
    *(코드상으로는 $\lambda$를 음수로 설정하여 $\lambda \sum x_i$ 보상을 주는 방식으로 동일하게 구현되어 있습니다.)*

*   **시간 중복 금지 ($E_{\text{overlap}}$):**
    시간이 겹치는 두 과목 쌍의 집합을 $O$라고 할 때, 둘 다 선택되는 것을 강력히 금지합니다.
    $$E_{\text{overlap}} = \lambda_{\text{over}} \sum_{(i,j) \in O} x_i x_j$$

*   **우주공강 기피 ($E_{\text{tension}}$):**
    같은 요일(집합 $S$)에 배치된 두 과목 사이의 시간 간격(gap)이 60분 초과 일 때 부과되는 페널티입니다. $e_{i,j}$는 시간 간격의 제곱근($\sqrt{\text{gap}}$)으로 정의됩니다.
    $$E_{\text{tension}} = \lambda_{\text{ten}} \sum_{(i,j) \in S} e_{i,j} x_i x_j$$

*   **연강 선호 ($E_{\text{contig}}$):**
    같은 요일(집합 $S$)에 배치된 두 과목 사이의 시간 간격이 60분 이하 일 때 주어지는 보상(음의 페널티)입니다. $f_{i,j}$는 연강 성립 여부에 따른 가중치입니다.
    $$E_{\text{contig}} = \lambda_{\text{con}} \sum_{(i,j) \in S} f_{i,j} x_i x_j$$

### 2.2 부가적인 소프트 & 공강 에너지 항 (Additional Soft & Free Day Terms)

*   **개별 과목 소프트 페널티 ($E_{\text{soft}}$):**
    1교시($P_{\text{1st}}$), 점심시간 겹침($P_{\text{lunch}}$), 시간 대비 학점 불균형($P_{\text{mis}}$) 등에 대해 각각의 상수 $\lambda$를 일차항에 부과합니다.
    $$E_{\text{soft}} = \sum_i \left( \lambda_{\text{1st}} P_{\text{1st},i} + \lambda_{\text{lunch}} P_{\text{lunch},i} + \lambda_{\text{mis}} P_{\text{mis},i} \right) x_i$$

*   **공강 요일 확보 ($E_{\text{free}}$):**
    요일 $d$가 공강임을 나타내는 보조 변수 $y_d$를 활용합니다. $D_d$는 요일 $d$에 개설되는 모든 과목의 집합입니다. 공강에 대한 보상($\lambda_{\text{fb}}$)과 모순 발생 시의 페널티($\lambda_{\text{fp}}$, 여기서 $\lambda_{\text{fp}} \gg \lambda_{\text{fb}}$)항의 합으로 구성됩니다.
    $$E_{\text{free}} = - \lambda_{\text{fb}} \sum_d y_d + \lambda_{\text{fp}} \sum_d \sum_{i \in D_d} x_i y_d$$

## 3. 최적화 파이프라인 흐름 (Optimization Flow)

1.  **후보군 축소 (`quantum_optimizer.py`):** 
    *   성능 확보를 위해 전체 강의를 대상으로 하지 않고, 사용자가 지정한 필수 과목 + 선택 가능한 후보(토요일 제외 등의 조건 적용)를 추려 최대 약 300개의 BQM 변수 풀을 구성.
2.  **BQM 모델 빌드 (`bqm_builder.py`):**
    *   개별 강의의 Linear Biases(일차항 가중치)를 계산하여 모델에 추가.
    *   목표 학점을 맞추기 위한 전역 쌍 상호작용(Quadratic Biases) 계산.
    *   시간 복잡도 O(N^2)을 줄이기 위해 요일별로 묶어(O(N_day^2)) 시간 충돌, 연강/우주공강, 공강 여부 모델 검증 및 이차항 할당.
3.  **Simulated Annealing 샘플링 (`quantum_optimizer.py`):**
    *   C++ 기반의 `neal.SimulatedAnnealingSampler` 또는 파이썬 내장 `dimod.SimulatedAnnealingSampler`를 통해 배치를 나누어 모델 샘플링을 진행.
    *   가장 낮은 에너지 상태(Energy Minimum)를 가지는 해를 찾아 조건 위배가 가장 적은 유니크한 시간표 조합 Top 5를 반환.
