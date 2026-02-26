# Timetable Optimization Quantum Annealing (Simulated Annealing) Model Summary

This project formulates the timetable generation problem as a **QUBO (Quadratic Unconstrained Binary Optimization)** model and uses **Simulated Annealing** (a heuristic search algorithm based on MCMC) to find the optimal timetable combination. We construct the BQM (Binary Quadratic Model) in a Python environment and derive solutions using the `dimod` and `neal` libraries.

## 1. Variables Definition

The binary variables targeted for optimization consist of two types:

*   $x_i \in \{0, 1\}$: Whether subject $i$ is selected (1: Selected, 0: Not selected)
*   $y_d \in \{0, 1\}$: Whether day $d$ is a free day (1: Free day, 0: Has classes)

## 2. Objective Function Details

The final objective function (energy $E$) of this timetable optimization model is composed of the sum of several consideration variables.
We express the total energy as a linear combination of each constraint as follows:

$$E = E_{\text{target}} + E_{\text{mandatory}} + E_{\text{overlap}} + E_{\text{tension}} + E_{\text{contig}} + E_{\text{soft}} + E_{\text{free}}$$

A lower energy value (Energy Minimum) is considered the optimal timetable. Here, $x_i, x_j, y_d \in \{0, 1\}$.

### 2.1 Main Energy Terms

Formulating the constraints of our project mathematically according to the provided formula format:

*   **Target Credits ($E_{\text{target}}$):**
    Induces reaching the target credits $T$ desired by the user. $c_i$ is the credit of subject $i$.
    $$E_{\text{target}} = \lambda_{\text{credit}} \left(\sum_i c_i x_i - T\right)^2$$

*   **Mandatory Classes ($E_{\text{mandatory}}$):**
    Subjects included in the mandatory subject set $M$ chosen by the user must be taken. (Penalty if not selected)
    $$E_{\text{mandatory}} = \lambda_{\text{man}} \sum_{i \in M} (1 - x_i)$$
    *(In the code, this is implemented equivalently by setting $\lambda$ to a negative value to give a reward of $\lambda \sum x_i$.)*

*   **Time Overlap Prohibition ($E_{\text{overlap}}$):**
    Let $O$ be the set of pairs of subjects with overlapping times; selecting both is strongly prohibited.
    $$E_{\text{overlap}} = \lambda_{\text{over}} \sum_{(i,j) \in O} x_i x_j$$

*   **Tension Model (Avoiding large gaps) ($E_{\text{tension}}$):**
    A penalty imposed when the time gap between two subjects placed on the same day (set $S$) exceeds 60 minutes. $e_{i,j}$ is defined as the square root of the time gap ($\sqrt{\text{gap}}$).
    $$E_{\text{tension}} = \lambda_{\text{ten}} \sum_{(i,j) \in S} e_{i,j} x_i x_j$$

*   **Contiguous Preference ($E_{\text{contig}}$):**
    A reward (negative penalty) given when the time gap between two subjects on the same day (set $S$) is 60 minutes or less. $f_{i,j}$ is the weight according to whether it is contiguous.
    $$E_{\text{contig}} = \lambda_{\text{con}} \sum_{(i,j) \in S} f_{i,j} x_i x_j$$

### 2.2 Additional Soft & Free Day Energy Terms

*   **Individual Subject Soft Penalties ($E_{\text{soft}}$):**
    We apply a constant $\lambda$ to the linear term for the 1st period ($P_{\text{1st}}$), lunch time overlap ($P_{\text{lunch}}$), time-to-credit mismatch ($P_{\text{mis}}$), respectively.
    $$E_{\text{soft}} = \sum_i \left( \lambda_{\text{1st}} P_{\text{1st},i} + \lambda_{\text{lunch}} P_{\text{lunch},i} + \lambda_{\text{mis}} P_{\text{mis},i} \right) x_i$$

*   **Free Day Logic ($E_{\text{free}}$):**
    Utilizes an auxiliary variable $y_d$ indicating that day $d$ is a free day. $D_d$ is the set of all subjects offered on day $d$. It consists of the sum of the reward for a free day ($\lambda_{\text{fb}}$) and a penalty when a contradiction occurs ($\lambda_{\text{fp}}$, where $\lambda_{\text{fp}} \gg \lambda_{\text{fb}}$).
    $$E_{\text{free}} = - \lambda_{\text{fb}} \sum_d y_d + \lambda_{\text{fp}} \sum_d \sum_{i \in D_d} x_i y_d$$

## 3. Optimization Flow

1.  **Candidate Pool Reduction (`quantum_optimizer.py`):** 
    *   To ensure performance, instead of targeting all lectures, it builds a BQM variable pool of up to about 300 by selecting the user-specified mandatory classes + selectable candidates (applying conditions like excluding Saturdays).
2.  **BQM Model Build (`bqm_builder.py`):**
    *   Calculates Linear Biases (first-order weights) of individual lectures and adds them to the model.
    *   Calculates global pair interactions (Quadratic Biases) to meet the target credits.
    *   To reduce time complexity O(N^2), it groups by day (O(N_day^2)) to verify time conflicts, contiguous/tension gaps, free day status and assigns quadratic terms.
3.  **Simulated Annealing Sampling (`quantum_optimizer.py`):**
    *   Proceeds with model sampling by dividing into batches using the C++ based `neal.SimulatedAnnealingSampler` or Python's built-in `dimod.SimulatedAnnealingSampler`.
    *   Finds the solution with the lowest energy state (Energy Minimum) and returns the Top 5 unique timetable combinations with the fewest condition violations.
