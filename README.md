# CP4-Dynamic

Checkpoint 4 — Graphs, Greedy strategies and Dynamic Programming applied to two real-world
problems: emergency logistics after climate events (Question 1) and energy consumption
management (Question 2).

## Team

| Name | RM |
|---|---|
| Thomas Sievers | 563566 |
| Marco Aurélio | 563827 |
| Áurea Sardinha | 563837 |
| Matheus Vasques | 563309 |
| Bernardo Hanashiro | 565266 |

## Reproducibility

`SEED = 1`. Developed and tested with Python 3.12 (random-number streams are only guaranteed
reproducible on the same Python version).

# Question 1 — Emergency Logistics

### 1 Problem

A civil-defense team runs a single distribution center with limited supplies (water, medicine,
food, hygiene kits, blankets) and one vehicle to serve up to 20 affected service points. Each
point has an affected population, a priority level, a minimum demand per resource, an expected
benefit, and roads to other points that may be unavailable (blocked). The graph is not fully
connected, and some roads are declared unavailable. Given a vehicle load capacity, the goal is to
choose which points to serve — and in what order — to maximize total benefit, using two
different strategies (Greedy and Dynamic Programming) and comparing them honestly, including a
case where Greedy is *not* optimal.

### 2 Adopted model

The full model and every trade-off are recorded as a decision log in `claude/SPEC.md` (Section
3, decisions D1–D15); the short version:

- **Graph**: 1 depot (node 0) + 20 candidate sites, roads with an integer distance, some marked
  unavailable. Distances between any two nodes are shortest-path distances over *available*
  roads only, computed by our own Dijkstra (D6).
- **Capacity**: one integer "load unit" capacity `C` per vehicle trip; a site's load is the sum
  of its five demands (D1). Service is all-or-nothing per site (0/1, D2) — no partial deliveries.
- **Route**: a single open trip, depot → site → … → site, no return leg, no multiple trips (D3).
- **Objective**: `J(S) = sum(effective_benefit) - lambda * L(S)`, where `effective_benefit =
  expected_benefit * priority` (D10) and `L(S)` is the route length of set `S` visited in a
  fixed canonical order `pi` (D5). `pi` is the pre-order DFS of the depot's shortest-path tree
  (D9) — sites in the same branch stay consecutive, so a compact cluster is cheap to visit.
  `lambda` is a fixed integer, calibrated once from the real dataset
  (`median(effective_benefit) / median(distance from the depot)`, D11): **21** for `SEED = 1`.
- Both Greedy and DP optimize this exact same `J(S)` (D4), so any gap between their results comes
  only from the strategy, not from a different objective.

### 3 Data structures

Justified by the operation each one makes cheap (Section 5.2 of `claude/SPEC.md`):

| Structure | Used for | Why |
|---|---|---|
| `dict[int, list[tuple[int, int]]]` (`Graph`) | adjacency list | O(1) access from a node to its neighbors |
| `set` | occupied grid positions, blocked-road check, visited/eligible candidates | O(1) membership test |
| `heapq` (binary heap) | Dijkstra's frontier | O(log n) extract-min |
| `collections.deque` | BFS connectivity check while blocking roads | O(1) `popleft` |
| `tuple` (frozen dataclasses) | `Site`, `Edge`, `Depot`, `Instance`, `Solution` | immutable value objects, safe to reuse/compare |
| `list[list[float]]` | the DP table `dp[i][c]` | dense table: most `(site, load)` states are populated |
| `dict[int, dict[int, float]]` | the all-pairs distance matrix | sparse-by-source access, one Dijkstra result per key |

### 4 Algorithms

- **Greedy** (`src/greedy.py`, D12): repeatedly serve the not-yet-chosen, capacity-fitting site
  with the highest marginal-benefit density `delta_J_i(S) / load_i`; stop when no site has
  positive marginal gain. Locally optimal for the *fractional* relaxation (an exchange argument:
  swapping a chosen item for a lower-density one cannot improve the result), but the 0/1
  restriction means leftover capacity after the best-density pick can be wasted — exactly where
  it can lose to DP (Part D).
- **Dynamic Programming** (`src/dynamic_programming.py`, Section 4): bottom-up DP over states
  `dp[i][c]` = best `J` for a route ending at the `i`-th site of `pi` with load exactly `c`.
  Base case `dp[i][w_i] = b_i - lambda * d(depot, site_i)`; recurrence considers every earlier
  site `j < i` as the direct predecessor. Full state/decision/base-case/recurrence/reconstruction
  explanation is in the module's docstring and in `docs/analise_complexidade.md`.
- Both return the same `Solution` shape (D15: no `Strategy`/`ABC` — plain functions), so Part D
  can compare them directly.

### 5 How to run

```bash
# 1. Create an environment with Python >= 3.10 and install dependencies
python3 -m venv .venv   # or: uv venv --python 3.12 .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. (Re)generate the dataset from SEED = 1 (data/problema1.csv, problema1_edges.csv)
python -m src.data_generator

# 3. Run the tests
pytest -q

# 4. Regenerate the figures (figures/questao1/*.png)
python -m src.plots

# 5. Run the notebook end to end
jupyter nbconvert --to notebook --execute notebooks/questao1.ipynb --output questao1.ipynb
```

### 6 Results

On the seed-1 dataset, default capacity `C = 581` (`floor(0.35 * 1662)`), `lambda = 21`:

| | Sites served | Total benefit | Total load | Route length | J(S) |
|---|---:|---:|---:|---:|---:|
| Greedy | 8 | 15565 | 564 | 318 | **8887** |
| DP (optimal) | 7 | 17439 | 580 | 274 | **11685** |

DP strictly outperforms Greedy on the real dataset (gap = 2798): Greedy's density-first pick
leaves capacity that DP fills with a better combination. A small hand-built counterexample
(3 sites, capacity 10, `lambda = 1`) makes the failure exact and provable by hand: Greedy takes
the single best-density site (`J = 59`) and then can't fit anything else, while DP takes the
other two sites together (`J = 88`) — see `docs/analise_complexidade.md` and
`tests/test_questao1.py` (`test_case_2_...`, `test_case_3_...`) for the full trace. The four
figures (service network, DP service plan, DP evolution table, time-growth comparison) are in
`figures/questao1/` and walked through in `notebooks/questao1.ipynb`.

### 7 Complexity

Full derivation in `docs/analise_complexidade.md`. Summary, in the problem's own parameters
(`V = 21`, `E = 38` for seed 1, `N` = candidate sites, `C` = capacity):

- **Greedy**: `O(N^3)` time (N rounds x N candidates x O(N) marginal-gain lookup), `O(N)` memory.
- **DP**: `O(N^2 * C)` time (`N * (C+1)` states x up to `N` predecessors each), `O(N * C)`
  memory — pseudo-polynomial in `C`. Unlike a classic 0/1 knapsack, this DP's recurrence lets
  *any* earlier site (not just the immediately preceding one) be a direct predecessor, so it
  cannot be reduced to an `O(C)` rolling vector even ignoring reconstruction.
- Preprocessing (Dijkstra + the full distance matrix + `pi`) is `O(N * (V+E) log V)`, negligible
  next to the DP at this scale (measured under a millisecond vs. ~5 ms for the DP itself).

### 8 Limitations

- **Single-resource capacity** (D1): a site's five separate demands are collapsed into one load
  number, so the model cannot express "enough water but no blankets"; a true multi-resource
  version would be a multidimensional knapsack.
- **0/1 service** (D2): no partial deliveries, even though it is what makes the DP well-defined
  and the Greedy failure mode possible.
- **One vehicle, one open trip, no return** (D3): a simplification of real multi-trip routing
  (VRP), which is NP-hard and out of scope here.
- **Route-of-a-set convention** (D5): `J(S)` is computed with sites visited in the fixed order
  `pi`; for a given set `S`, a better visiting order might exist. The DP is exact *for this `J`*,
  not for the unconstrained best route of every possible `S`.
- **`lambda` is fixed**, not re-calibrated if the dataset changes at run time (D11) — changing
  weights live during the defense will not automatically re-tune it.

# Question 2 — Energy Consumption Management

Owner: Marco Aurélio

### 1 Problem

_TODO_

### 2 Adopted model

_TODO_

### 3 Data structures

_TODO_

### 4 Algorithms

_TODO_

### 5 How to run

_TODO_

### 6 Results

_TODO_

### 7 Complexity

_TODO_

### 8 Limitations

_TODO_

## Final question (max 300 words)

_TODO: paste the exact final-question prompt from the assignment
(`Checkpoint_4_turma_W_21SET26`) here._

_TODO_
