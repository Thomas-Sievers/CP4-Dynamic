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

`SEED = 1` — our group's assigned identifier, used as the RNG seed for both datasets (`SEED =
numero_do_grupo`). Developed and tested with Python 3.12 (random-number streams are only
guaranteed reproducible on the same Python version).

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

A simplified power grid records hourly consumption readings from several regions
(`timestamp`, `regiao`, `consumo`, `capacidade_disponivel`, `prioridade`, `custo`). The goal is
to find the single **continuous** time interval with the highest accumulated **criticality** —
the worst stretch of time the grid went through — using two different strategies (brute force
and divide-and-conquer) and comparing them.

### 2 Adopted model

- **Dataset** (`src/gerar_dataset.py`): 1,200 synthetic hourly readings (10 days x 5 regions),
  documented and reproducible with `SEED = 1`.
- **Injected critical event**: region Sul has its available capacity cut in half for a
  continuous 30-hour window (simulating an outage/maintenance), while every region's capacity
  is otherwise sized at 2x its base consumption so ordinary daily peaks stay safely under it.
  Without a deliberate event like this, daily peaks repeat too evenly across all 10 days and the
  "most critical interval" degenerates to almost the entire dataset (see Limitations).
- **Criticality function** (`src/criticidade.py`):
  `criticidade = consumo_relativo + penalidade_por_excesso`, where
  `consumo_relativo = consumo - capacidade_disponivel * 0.75` (negative while a reading stays
  under 75% of *its own* capacity, which normalizes the score across regions of very different
  scale) and `penalidade_por_excesso = max(0, consumo - capacidade_disponivel) * 2.0 *
  prioridade` (only nonzero once capacity is actually exceeded; priority multiplies the excess
  instead of adding a flat bias, so a region only weighs more when it is genuinely overloaded).
  This departs from the assignment's literal example (`consumo + penalidade + prioridade`)
  because an always-nonnegative score makes the maximum-accumulated-interval search trivial.

### 3 Data structures

| Structure | Used for | Why |
|---|---|---|
| `list[dict]` (`carregar_leituras`) | ordered readings, indexable by position | O(1) access by index / O(k) slicing — what both search algorithms use to select a continuous interval |
| `set[str]` (`regioes_existentes`) | distinct region names | O(1) membership test vs. O(n) scan |
| `dict[str, list[dict]]` (`agrupar_por_regiao`) | consumption by region | O(1) lookup by key vs. O(n) scan |
| `dict[int, list[dict]]` (`agrupar_por_horario`) | consumption by hour of day | O(1) lookup by key, independent of region |
| `dict[tuple[str, int], list[dict]]` (`agrupar_por_regiao_e_hora`) | consumption by region + hour | `tuple` as a hashable composite key — a `list` could not be used as a dict key |
| `heapq.nlargest` (`maiores_picos_de_consumo`) | top-k consumption peaks | O(n log k) instead of sorting everything (O(n log n)) |

### 4 Algorithms

- **Brute force** (`src/brute_force.py`): two nested loops explicitly test every `(start, end)`
  pair — no shortcut, no library max-subarray function.
- **Divide and conquer** (`src/divide_conquer.py`): the classic maximum-subarray recursion
  adapted to criticality — base case (single reading), split the range in half, solve the left
  half, solve the right half, solve the case that crosses the split
  (`_melhor_intervalo_cruzando_o_meio`: two linear scans outward from the midpoint), then combine
  (pick the best of the three candidates). `T(n) = 2T(n/2) + O(n) = O(n log n)` by the master
  theorem.
- Both call the same `calcular_criticidade` and always return the exact same interval (checked
  by `tests/test_questao2.py` and side by side in `notebooks/questao2.ipynb`).

### 5 How to run

```bash
pip install -r requirements.txt

# regenerate the dataset (SEED = 1) -> data/problema2.csv
python src/gerar_dataset.py

# run either algorithm directly
python -m src.brute_force
python -m src.divide_conquer

# scalability experiment (n = 100..5000) -> data/escalabilidade.csv
python -m src.experimento_escalabilidade

# regenerate the three figures -> figures/questao2/*.png
python -m src.grafico_serie_temporal
python -m src.grafico_arvore_decomposicao
python -m src.grafico_escalabilidade

# tests
pytest tests/test_questao2.py -v

# full notebook, end to end
jupyter nbconvert --to notebook --execute notebooks/questao2.ipynb --output questao2.ipynb
```

### 6 Results

On the seed-1 dataset (1,200 readings), both algorithms find the exact same interval:

| | Interval (indices) | Period | Readings | Criticality |
|---|---:|---|---:|---:|
| Brute force | [571, 586] | 2025-06-05 18:00 to 21:00 | 16 | **1873.20** |
| Divide and conquer | [571, 586] | 2025-06-05 18:00 to 21:00 | 16 | **1873.20** |

This matches exactly the injected critical event (region Sul, capacity cut in half).
Scalability (`data/escalabilidade.csv`, each row one run at that `n`):

| n | Time — FB (s) | Time — DC (s) | Operations — FB | Operations — DC | Memory — FB (bytes) | Memory — DC (bytes) |
|---:|---:|---:|---:|---:|---:|---:|
| 100 | 0.000246 | 0.000172 | 5,050 | 664 | 1,048 | 1,160 |
| 250 | 0.001352 | 0.000392 | 31,375 | 1,991 | 5,928 | 6,064 |
| 500 | 0.005839 | 0.000839 | 125,250 | 4,483 | 14,092 | 15,128 |
| 1,000 | 0.024137 | 0.001806 | 500,500 | 9,966 | 31,539 | 32,048 |
| 2,000 | 0.109495 | 0.003657 | 2,001,000 | 21,932 | 62,068 | 63,496 |
| 5,000 | 0.604972 | 0.009821 | 12,502,500 | 61,439 | 160,596 | 161,504 |

The most reliable comparison is `n = 1,000 -> 5,000` (5x): brute force gets **~25.1x** slower in
time and its operation count grows **~25.0x** (500,500 -> 12,502,500) — matching `5^2 = 25`,
i.e. `O(n^2)`. Divide-and-conquer gets only **~5.4x** slower in time and **~6.2x** in operation
count (9,966 -> 61,439) — close to the `O(n log n)` prediction of
`5 * log(5000)/log(1000) ~= 6.2x`, far below brute force's 25x. Memory grows **~5.0-5.1x** for
*both* algorithms (matching `n` growing 5x), confirming the `O(n)` `scores` array — not the
`O(log n)` recursion stack — dominates divide-and-conquer's memory too (Section 7). The wider
`n = 100 -> 5,000` span (50x) points the same direction (brute force ~2,459x slower, DC ~57x),
but with sub-millisecond timings at `n = 100` that ratio is noisier and is kept only as
supporting context, not as the number the `O(n^2)`/`O(n log n)` claim rests on. Figures and full
interpretation are in `figures/questao2/` and walked through in `notebooks/questao2.ipynb`.

### 7 Complexity

Full derivation in `docs/analise_complexidade.md`. Summary:

- **Brute force**: `T(n) = O(n^2)` (two nested loops over every interval pair), `S(n) = O(n)`
  (the `scores` array).
- **Divide and conquer**: `T(n) = O(n log n)` (`T(n) = 2T(n/2) + O(n)`, master theorem),
  `S(n) = O(n)` (the `scores` array dominates the `O(log n)` recursion stack).
- Growing from 1,000 to 1,000,000 readings: brute force projects to **~24,000s** (~6.8h,
  infeasible); divide-and-conquer projects to **~3.4s** (still viable) — only divide-and-conquer
  scales.

### 8 Limitations

- **Synthetic dataset, single injected event**: real utility data would likely show several,
  possibly overlapping critical events across regions; this dataset injects only one, in one
  region, to keep the demonstration legible.
- **Criticality thresholds are our own choice, not regulatory**: `LIMIAR_SEGURO = 0.75` and
  `FATOR_PENALIDADE_EXCESSO = 2.0` (`src/criticidade.py`) were picked to make the search
  meaningful (avoid the degenerate "whole dataset" answer), not derived from a real grid
  operator's safety standard.
- **Region-interleaved sequence**: `carregar_leituras()` keeps the CSV's row order (five
  regions per hour, in timestamp order); a "continuous interval" is contiguous in that list, not
  on a single per-region time axis, so a found interval can span multiple regions within the
  same hour block rather than only consecutive hours of one region.
- **Memory measurement** (`tracemalloc`) only captures Python-level heap allocations, not
  C-level buffers.
- **Scalability experiment uses synthetic random readings**, not the real 1,200-row dataset,
  because `n` goes up to 5,000 (above the dataset's size); timing is representative, but the
  specific readings measured are not the real ones.

## Final question (max 300 words)

_Qual foi a decisão algorítmica mais importante tomada pelo grupo? Apresente uma alternativa que
vocês descartaram e explique, considerando tempo, memória e qualidade da solução, por que a
abordagem escolhida foi considerada mais adequada._

A decisão mais importante foi a forma da recorrência da DP da Questão 1: em vez da mochila 0/1
clássica (`dp[i][c] = max(dp[i-1][c], dp[i-1][c-w_i] + b_i)`, onde o predecessor de cada item é
sempre a linha `i-1`), permitimos que **qualquer** site anterior `j < i` na ordem canônica `pi`
seja o predecessor direto de `i` (`src/dynamic_programming.py`, Seção 4 do README).

A alternativa descartada — a mochila clássica — seria mais barata: `O(N*C)` em tempo, contra o
`O(N^2*C)` da versão escolhida (Seção 7), e poderia até ser reduzida a um vetor rolante `O(C)`
de memória. Descartamos porque ela é **incorreta** para o nosso `J(S)`: como o benefício
depende do comprimento da rota `L(S)`, que soma distâncias entre sites *efetivamente visitados*
em sequência, a transição "pular o site `i-1`" da mochila clássica perde a informação de qual
foi o último site realmente visitado — e é exatamente isso que a distância do próximo trecho
precisa. Isso não é hipotético: a solução ótima real atende só 7 dos 20 sites candidatos
(Seção 6), ou seja, a maioria das transições da rota "pula" vários sites da ordem `pi`, e a
mochila clássica computaria uma `L(S)` errada nesses casos.

Em tempo, a diferença é irrelevante na prática (a DP inteira mede ~5ms para N=20, Seção 7); em
memória, ambas as versões precisam guardar a tabela completa para permitir a reconstrução
(Parte C), então não há perda real de memória ao escolher a recorrência mais cara. A única
dimensão em que a alternativa descartada realmente vencia — tempo assintótico — não compensava
o custo em qualidade da solução: preferimos uma resposta comprovadamente ótima a uma resposta
rápida e errada. É também essa recorrência mais expressiva que produz o contraexemplo real do
grupo (Seção 6): Greedy erra por 2.798 em `J(S)` justamente porque, ao contrário da DP, não
enxerga essa dependência entre sites não-adjacentes na rota.
