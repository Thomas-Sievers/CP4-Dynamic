# SPEC — Checkpoint 4, Question 1 (Emergency Logistics after Climate Events)

> Spec Driven Design document. Language: English (code, comments, docstrings, docs).
> Only the file/folder names required by the assignment stay in Portuguese
> (`questao1.ipynb`, `problema1.csv`, `test_questao1.py`, `analise_complexidade.md`, ...).

---

## 0. Rules for the implementing agent (Claude Code)

1. **Implement only the step you are told to implement** (see Section 7). Do not create
   files, functions or tests that belong to a later step, even if they look obvious.
2. **Do not run `git commit`, `git push`, `git rebase` or anything that changes history.**
   The team commits manually, step by step, to show progressive development.
3. **Never overwrite existing content.** Inspect the repository first; only add what is missing.
4. **Sections marked `TBD` are undecided.** Do not invent a decision for them. Stop and ask.
5. **Do not touch Question 2 files** (`brute_force.py`, `divide_conquer.py`,
   `test_questao2.py`, `questao2.ipynb`, `problema2.csv`, `figures/questao2/`). They are
   owned by another team member.
6. **Follow Section 5.2 (Course alignment guide).** The code must look like the course
   notebooks; do not introduce styles, patterns or libraries the course does not use.
7. **Explainability over cleverness.** Every team member must be able to explain any function
   in an oral defense. Prefer simple loops over tricks. Every non-trivial function needs a
   docstring stating *what* it does and *why* the chosen approach is appropriate. Comments
   explain the reasoning, not the syntax.
8. **Forbidden for the core algorithms:** `networkx` (any use), `scipy.optimize`, `pulp`, and
   any ready-made shortest-path / knapsack / optimization solver. Graph, Dijkstra, Greedy and DP are
   implemented by the team. Python's standard `heapq` **is allowed** (it is a data structure,
   not the algorithm).
9. **Dependencies:** standard library first. Any third-party package must be listed in
   `requirements.txt` with a one-line justification comment.
10. After finishing a step, report: files created/changed, how to run the tests, and any
   assumption you had to make.

---

## 1. Assignment summary (source of truth: `Checkpoint_4_turma_W_21SET26`)

Group work, deadline **21/SEP/2026 23:59 (Teams)**. One GitHub repository containing both
questions. This spec covers **Question 1 only**.

A civil-defense team has one distribution center with limited supplies (water, medicine, food,
hygiene kits, blankets) and several service points, each with: affected people, priority
level, minimum demand, expected benefit, distances to other points, and possibly blocked roads.
The problem is modeled as a **weighted graph**.

| Part | Requirement |
|---|---|
| A | Dataset with **≥ 20 service points, 1 distribution center, ≥ 35 connections**, a distance/cost per connection, priority, required resources, expected benefit. Graph **not fully connected**; some roads declared **unavailable**. Justify every data structure by the operations the algorithm performs. |
| B | Greedy strategy with **our own priority function**, justified mathematically or algorithmically. A rule like `highest_priority_first()` is not enough. |
| C | Dynamic Programming choosing the combination of services that maximizes total benefit within vehicle capacity. Must explain: **state, decision, base case, recurrence, reconstruction**. A filled matrix alone is not accepted. |
| D | Run Greedy and DP on the same data. Show cases where Greedy is optimal, where Greedy is not optimal, and where DP is superior. **At least one counterexample built by the group** where the greedy decision is not optimal, with an exact explanation. |
| E | At least **3 figures**: (1) graph with depot, points, connections, weights, blocked roads; (2) solution: served / not served points and the service path/sequence; (3) DP evolution (matrix, heatmap, decision reconstruction or benefit-vs-capacity). Figures must explain the algorithm. |
| F | Time and space complexity using problem parameters (V, E, N, C), explaining where each term comes from. A bare `O(n²)` table is rejected. |

Other hard requirements: reproducible data via `SEED`, progressive commits, tests, README with
8 sections, final README question (≤ 300 words), individual explanation ability, input
changes during the presentation (weight, capacity, priority, connection, interval), surprise
test case.

---

## 2. Team and reproducibility

| Name | RM |
|---|---|
| Thomas Sievers | 563566 |
| Marco Aurélio | 563827 |
| Áurea Sardinha | 563837 |
| Matheus Vasques | 563309 |
| Bernardo Hanashiro | 565266 |

- **`SEED = 1`** (group identifier, confirmed with the course on Teams).
- The seed must live in **one single place** in the code (a constant in the data generator
  module, created in Step 2) and be recorded in the README. Changing it must regenerate the
  whole dataset and every result.

---

## 3. Decision log

Each decision records what was chosen, why, and the trade-off. The team must be able to
defend all of them orally, and they feed the final README question.

### D1 — Single capacity in integer "load units"
- **Decision:** the vehicle has one capacity `C`. Each site's load `w_i` is the integer sum of
  its demands over the 5 resource types (per-resource detail stays in the CSV).
- **Strength:** fits a `DP[i][c]`-style table; cost is polynomial in `N` and `C`.
- **Weakness:** cannot express "enough water but no blankets". Multi-resource capacity would be
  a multidimensional knapsack (state explodes). Goes in the README *Limitations*.
- **Note:** cost is **pseudo-polynomial** because it depends on the *value* of `C`, not on its
  number of bits. Keep load units small integers (hundreds), never grams.

### D2 — 0/1 service (all or nothing)
- **Decision:** a site is either fully served (its whole demand is delivered) or not served.
- **Strength:** consistent with the "minimum demand" statement; makes the DP well-defined and
  explains why Greedy can fail (unused leftover capacity).
- **Weakness:** no partial deliveries. On the *fractional* knapsack the ratio-greedy is provably
  optimal; the 0/1 restriction is exactly what breaks it.

### D3 — One vehicle, one trip, no return to the depot
- **Decision:** a single open route: depot → first site → … → last site. No return leg, no
  multiple trips, no distance limit besides capacity.
- **Strength:** clean, explainable model; multi-trip routing (VRP) is NP-hard and out of scope.
- **Weakness:** the model is a simplification of real operations. Goes in *Limitations*.

### D4 — Set-dependent cost, one objective `J(S)` shared by Greedy and DP
- **Decision:** the cost of serving a site depends on which other sites are served (a compact
  cluster is cheap, an isolated far site is expensive). Both algorithms optimize the **same**
  objective (Section 4), so any gap between them comes from the *strategy*, not from different
  criteria.
- **Strength:** fair Greedy × DP comparison; the counterexample is clean.
- **Weakness:** introduces the parameter `λ` and forces a route definition (D5).

### D5 — Route of a set: canonical order `π` (option A)
- **Decision:** a fixed total order `π` over candidate sites is defined once. Any set `S` is
  visited **in increasing `π` order**. This makes `J(S)` well-defined and lets the DP be
  **exact for `J`**.
- **Strength:** DP state `(last site, load)` with cost `O(N²·C)`; guarantees `DP ≥ Greedy`
  under the same `J`. Easy to explain (path DP over a DAG defined by `π`).
- **Weakness:** for a given set, a better visiting order may exist; the "optimal" plan is
  optimal *under the `π` route convention*. Goes in *Limitations*. The construction of `π` is
  fixed in **D9**.
- **Course link (defense argument):** `π` turns the candidate sites into a **DAG** (edge
  `j → i` whenever `j` comes before `i` in `π`). The DP then processes states in topological
  order and stores a `parent` per state — the same pattern as the DAG longest-path DP of
  Lessons 08 and 14 (`distance` / `parent`), with the load `c` as an extra dimension.
- **Rejected alternatives:** exact TSP-style DP over subsets (`O(2^N·N²)`, too slow and loses
  the `DP[i][c]` shape); tree-DP over the union of shortest paths (only an estimate of the real
  route cost, more code to defend).

### D6 — Distances come from our own Dijkstra
- **Decision:** `d(u, v)` is the shortest-path distance over **available** roads, computed by a
  team-implemented Dijkstra using a binary heap (`heapq`). Sites unreachable from the depot are
  excluded from the candidate set.
- **Strength:** respects blocked roads; complexity `O((V + E) log V)` per source.
- **Weakness:** the course material has no Dijkstra/heap/greedy; extra care is needed in
  comments and tests so the team can defend it.

### D7 — Counterexample as a separate small instance
- **Decision:** the Greedy counterexample is a **small hand-built instance** (a few sites)
  under the `J(S)` model, solvable on paper, stored as a deterministic test. The full seed-1
  dataset is *also* run through both algorithms and whatever happens is reported honestly.
- **Strength:** the reason for the failure can be explained exactly.
- **Weakness:** a reviewer may ask "what about the real data?" — answered by the full-dataset
  comparison in Part D. Never change the seed to force a result.

### D8 — Language and structure
- **Decision:** all code, comments, docstrings, this spec and the team's README parts are in
  English. Assignment-mandated file names stay in Portuguese. The spec lives in `claude/`.
- **Weakness:** the professor evaluates in Portuguese; the team must be ready to explain the
  same terms in both languages during the defense.

### D9 — Canonical order `π`: pre-order DFS of the shortest-path tree
- **Decision:** run Dijkstra from the depot; its `parent` map is a tree over the reachable nodes.
  `π` is the **pre-order DFS of that tree** starting at the depot (the depot itself is not part
  of `π`). Children are visited sorted by `(distance from the depot, node_id)`. Sites not
  reachable from the depot are excluded from `π` and from the candidate set.
- **Strength:** sites of the same branch stay consecutive, so compact clusters are cheap to
  visit (the "A, B, C close together, Z far away" intuition); it uses only the graph, so it
  respects blocked roads; it reuses the recursive DFS taught in class; pre-order is a
  topological order of the tree (a junction is always visited before what lies beyond it).
- **Weakness:** slightly more to explain than sorting by distance (child ordering and the
  tie-break); like any `π`, it is not optimal for every instance (see D5).
- **Evidence (scratch prototype, 21 nodes; must be re-measured with the team's own data and
  reported in the README):** against the exact optimum over *all* visiting orders (N = 10,
  40 instances) distance-order reached ≈ 0.99, DFS ≈ 0.987 and angular sweep ≈ 0.94–0.98
  (worst case 0.498). With N = 20 (40 seeds), relative to the best of the three, DFS scored
  0.985–0.990 for `λ` = 10 and 20 and tied at `λ` = 40. Differences are ≈ 1 % either way.
- **Rejected alternatives:** ordering by distance from the depot (simplest, but it interleaves
  branches, so routes that mix clusters zigzag); angular sweep (needs coordinates, ignores the
  real road network and blocked roads, worst case far below the others).

### D10 — Benefit and load formulas
- **Decision:** `effective_benefit_i = expected_benefit_i × priority_i`, with integer
  `priority_i ∈ {1, …, 5}`; `load_i = water + medicine + food + hygiene_kits + blankets`
  (five non-negative integers). Both are **derived when loading** (properties of `Site`), not
  stored. All benefits, loads and distances are integers.
- **Strength:** editing `priority`, `expected_benefit` or any single demand changes the result,
  which supports the live input changes of the defense; integer data makes `J` exact (no
  floating-point ties or rounding in tests).
- **Weakness:** `expected_benefit` alone is not the benefit the algorithms use; this must be
  explained in the README.
- **Generation:** `expected_benefit = round(people_affected × U(0.6, 1.0))` ("people effectively
  assisted"), so it is genuinely separate data from `people_affected`.

### D11 — Distance price `λ`
- **Decision:** `λ` is a **fixed positive integer constant**, calibrated **once** with the rule
  `λ ≈ median(effective_benefit) / median(distance from the depot)` (rounded to an integer),
  documented in Step 3. It is **not** recomputed at run time. A sensitivity sweep over `λ` may
  be added as an extra figure in Part D.
- **Strength:** interpretable ("a median site is worth one median trip from the depot"); stable:
  in the prototype `λ` between 10 and 30 produced the same plan, `λ ≈ 5` made distance almost
  irrelevant and `λ ≈ 100` degenerated to a single site.
- **Weakness:** the value depends on the instance; recomputing it at run time would blur the
  effect of a weight changed by the professor, hence the fixed constant.

### D12 — Greedy score: benefit density under the shared `J`
- **Decision:** at each step, for every not-yet-chosen site `i` that fits the remaining
  capacity, compute the marginal gain `ΔJ_i` (Section 4) and the score `ΔJ_i / load_i`. Only
  sites with `ΔJ_i > 0` are eligible. Pick the highest score; **tie-break:** larger `ΔJ_i`, then
  smaller `load_i`, then smaller `node_id`. **Stop** when no eligible site remains.
- **Why it is locally advantageous:** capacity is the scarce resource, so we take the most
  gain per unit of capacity. In the *fractional* relaxation with fixed values this rule is
  optimal by an exchange argument (swapping a chosen item for one of lower density cannot
  improve the result); in the 0/1 problem the capacity left over after the best-density item
  may be wasted, which is exactly why Greedy can fail.
- **Weakness:** with set-dependent costs there is no optimality proof; it is a heuristic.
  In the prototype it was below the DP in about half of the instances (gap 1.7 %–4.6 % for
  `λ ≤ 20`) and the DP never lost to it.
- **Alternative to discuss in the README:** pure marginal gain `ΔJ_i` (no division by load). In
  the prototype it was slightly better for large `λ` (e.g. mean gap 4.3 % vs 6.5 % at
  `λ` = 40, capacity 35 %).

### D13 — Q1 modules in `src/`
One module per responsibility, each created **in the step that first needs it**:

| Module | Responsibility | Step |
|---|---|---|
| `estruturas.py` (mandated name) | `Depot`, `Site`, `Edge`, `Instance`, `Graph` type alias; `Solution` later | 2 (`Solution`: 3) |
| `data_generator.py` | `SEED`, deterministic generation, writing the CSV files | 2 |
| `data_loader.py` | reading and validating the CSV files into an `Instance` | 2 |
| `shortest_paths.py` | Dijkstra with `heapq`, path reconstruction, distance matrix | 2 |
| `objective.py` | order `π`; later route length, `J(S)`, marginal insertion cost | 2 (π), 3 |
| `greedy.py` (mandated) | Greedy solver | 3 |
| `dynamic_programming.py` (mandated) | DP solver | 4 |
| `plots.py` | figures | 6 |
| `measurements.py` | time and memory helpers | 7 |

- **Strength:** single responsibility per file (a stated quality criterion); progressive
  commits come naturally.
- **Weakness:** more files than the recommended tree (which is only a minimum).
- `estruturas.py` is shared with Question 2: Q1 code lives inside a clearly delimited block
  (`# ===== Question 1 =====` … `# ===== end Question 1 =====`); Question 2 adds its own block.
- Tests stay in a **single** `tests/test_questao1.py`.

### D14 — Data files and capacity
- **Decision:** two CSV files, one row per element:
  - `data/problema1.csv` — **nodes** (depot + sites);
  - `data/problema1_edges.csv` — **roads**, including the blocked ones.
  Capacity is **not** stored in the files: it is an argument of the solvers, with a default of
  `floor(CAPACITY_FRACTION × total load)` in the notebook. Together the two files are the
  complete dataset, and the README must say so.
- **Why not one single file:** nodes and roads are two different tables (about 21 rows × 13
  columns and 41+ rows × 4 columns). One file would need a `record_type` column and many empty
  cells, and the loader would have to branch per row. Capacity is not a property of the data
  but a parameter of the experiment (the professor may change it, Part D sweeps it), so
  storing one value would suggest it is fixed.
- **Weakness:** the assignment tree lists only `problema1.csv`; the second file is an addition.
  Switching to a single tagged file only changes the loader and the generator's writer.

### D15 — No `Strategy` / `ABC`
- **Decision:** `solve_greedy(...)` and `solve_dp(...)` are plain functions that return the
  same `Solution` dataclass, so the Part D comparison treats both uniformly. The DP also
  returns its table for Figure 3.
- **Strength:** simple; no abstraction without a client that swaps solvers at run time.
  The assignment states that classes created only to "use OOP" earn no points.
- **Weakness:** no formal polymorphism (Lessons 03 and 11 remain available as a reference).

---

## 4. Mathematical model (decided; `λ` value fixed in Step 3)

**Sites:** `0` = depot; `1..N` = candidate service sites, i.e. those reachable from the depot
through available roads. Each site `i` has an integer load `w_i = load_i > 0` and an integer
benefit `b_i = effective_benefit_i = expected_benefit_i × priority_i ≥ 0` (D10).

**Distances:** `d(u, v)` = shortest-path distance over available roads (Dijkstra). It satisfies
the triangle inequality `d(p, s) ≤ d(p, i) + d(i, s)`.

**Order and route of a set:** `π` is the order of D9. For `S = {s_1, s_2, …, s_k}` sorted by `π`:

```
L(S) = d(0, s_1) + d(s_1, s_2) + … + d(s_{k-1}, s_k)        (open route, no return)
```

**Objective (maximize):**

```
J(S) = Σ_{i∈S} b_i  −  λ · L(S)          subject to   Σ_{i∈S} w_i ≤ C
```

`J(∅) = 0`. `λ` is a fixed positive integer constant (D11) that converts distance into
benefit units.

**Marginal gain (used by Greedy).** Let `S` be the current set sorted by `π`, and `i ∉ S`.
Let `p` be the `π`-predecessor of `i` in `S` (or the depot `0` if there is none) and `s` its
`π`-successor in `S` (or none):

```
ΔL_i(S) = d(p, i) + d(i, s) − d(p, s)      if s exists
ΔL_i(S) = d(p, i)                          if i would be the last site
ΔJ_i(S) = b_i − λ · ΔL_i(S)
```

By the triangle inequality `ΔL_i(S) ≥ 0`. This is exactly `J(S ∪ {i}) − J(S)` under the `π`
route convention.

**DP formulation (Step 4, to be specified in detail then):**
- *State:* `DP[i][c]` = best value of `J` over routes that **end at site `i`** (in `π` order)
  with total load **exactly** `c`.
- *Decision:* which earlier site `j < i` (in `π`) precedes `i`, or `i` is the first site.
- *Base case:* `DP[i][w_i] = b_i − λ·d(0, i)`.
- *Recurrence:* `DP[i][c] = b_i + max_{j<i} ( DP[j][c − w_i] − λ·d(j, i) )`.
- *Answer:* `max(0, max_{i, c ≤ C} DP[i][c])`.
- *Reconstruction:* store the argmax predecessor `j` for each cell; walk back from the best cell.
- *Cost:* time `O(N²·C)`, space `O(N·C)`.

**Greedy (Step 3, to be specified in detail then):** the rule of D12, with `ΔJ_i(S)` as above.
Using the same `J` and the same `π` convention is what keeps the guarantee `DP ≥ Greedy`
valid. Its myopia (no lookahead, leftover capacity wasted) is the argument for the
counterexample.

---

## 5. Engineering conventions

### 5.1 General

- Python ≥ 3.10, type hints everywhere, numpy-style docstrings (as in the course notebooks).
- Small functions, single responsibility, no duplicated code, no global mutable state.
- Classes only where they add value (e.g. immutable `@dataclass(frozen=True, slots=True)` for
  `Site`/`Edge`, a `Graph` class that encapsulates the adjacency dict). No classes "to say we
  used OOP".
- Validate inputs and raise `ValueError` with clear messages (negative capacity, unknown node,
  non-positive load, etc.).
- Figures are **generated by code** and saved to `figures/questao1/`; nothing is hand-drawn.
- Plotting with `matplotlib` only, positioned with coordinates stored in the data (no
  `networkx`).
- Tests with `pytest`, deterministic (fixed seed / hand-built instances).
- Time measurement with `time.perf_counter`, memory with `tracemalloc` (standard library).
- Read the CSV files with the standard `csv` module (no `pandas`, to keep dependencies minimal).

### 5.2 Course alignment guide

The code must look like what was taught in class. **Do not introduce styles, patterns or
libraries that the course does not use, unless this spec says so.** Reference lessons are in
parentheses.

**Clean code**
- No hidden copies: never slice lists in loops or recursion (`values[1:]`); pass indices
  (Lesson 11).
- Never use a mutable default argument; use `None` and create the object inside (Graph notebooks).
- No global variables; encapsulate parameters and rules (Lesson 14).
- Every recursive or tabulated function states its **base case** explicitly, with a comment.
- Names describe the state: `memo`, `parent`, `distance`, `remaining_capacity`, `last_site`.
- Internal helpers start with `_`; use `@staticmethod` when the method does not use `self`
  (Lesson 09).
- Validate inputs at the top of the function with `raise ValueError("...")` (Lessons 03, 12).
- Small type aliases for readability, e.g. `Graph = dict[int, list[tuple[int, float]]]`
  (Lesson 14, `WeightedDAG`).

**Docstrings and complexity comments**
- numpy-style docstring with `Parameters`, `Returns`, `Raises` on every public function.
- DP/greedy docstrings describe the **state** (Lesson 12, `mochila_bottom_up`).
- Complexity is written next to the code, in the course format:

```python
# TIME: N·(C+1) states × up to N predecessors each -> O(N²·C).
# MEMORY: dp and parent tables, N×(C+1) each -> O(N·C).
```

**Classes vs functions**
- Class = clear domain entity or internal state (Lesson 09 `PlanejadorCaminhoDP`: `_dp`,
  `_predecessor`, `solve()`, `reconstruct_path()`, a `@property` for the result, a copy of the
  table for inspection). Pure computation = plain function (Lesson 11, "intentionally
  functional").
- `Strategy` / `ABC` for Greedy and DP (Lessons 03, 11) is **not used** (decision D15).

**Data-structure justification (Part A)**
- Each structure is justified by the operation it makes cheap, in the course's terms:
  `list` (append at the end, index access O(1)), `tuple` (immutable record / dict key),
  `dict` (access by key: adjacency list), `set` (membership: visited, blocked roads),
  `deque` (`popleft` O(1)), `heapq` (extract-min O(log n)).
- Dense DP table → list of lists; sparse states → `dict` with tuple keys `(i, c)`
  (Lesson 14 Advanced 2; B_DP notebook).

**DP explanation checklist (Part C)** — Lesson 12, section 9: state, decisions, base case,
transition, repeated states, safe fill order, reconstruction. Bottom-up is chosen over top-down
(no recursion stack, easy reconstruction, the table is Figure 3); justify with the Lesson 09
top-down vs bottom-up comparison.

**Big O analysis (Part F)** — each algorithm gets: time, space, and *where each term comes
from*. Required elements:
- The rule "time ≈ number of states × cost per transition" (Lesson 14).
- Explicit state count, e.g. `(N+1)(C+1)` (Lesson 12).
- Time **and** memory **and** recursion depth **and** temporary copies **and** worst case
  (Lesson 11, complexity synthesis) — never only time.
- Full table vs reduced vector (`O(N·C)` → `O(C)`) and what is lost (reconstruction).
- The pseudo-polynomial remark for `C`.
- Comparison with brute force `2^N` on a log scale (Lesson 12, Cell 07).
- Empirical measurements are trends, not proof: state that Big O describes growth, not
  seconds (Lesson 11, section 12).
- Checklist of common mistakes from Lesson 11 (confusing asymptotic and measured time,
  ignoring memory, classes without benefit).
- Parameters are the problem's own: `V`, `E`, `N`, `C`.

**Measurement (Lesson 11, Cells 13–14)**
- `measure_time(function, data, repetitions)` returns the **average** with `perf_counter`;
  data generated with `Random(seed)`; `peak_memory_bytes(function)` with `tracemalloc` inside
  `try/finally`, and a comment about its limits.

**Figures (Lessons 08, 09, 12)**
- Graph (Figures 1–2): `matplotlib` circles + `FancyArrowPatch`/lines, weights with a white
  background box, highlight color for the route and gray for the rest (Lesson 08
  `desenhar_dag`); blocked roads dashed and labeled in the legend.
- DP (Figure 3): `imshow` with the value written in each cell, labeled colorbar, reconstruction
  path drawn over the table, rectangles on decision cells, summary text box (Lesson 12,
  Cell 09).
- Titles and axis labels always present; `figsize` around (9, 5.5); log scale for growth.

**Code returns data; the notebook shows it**
- Library functions in `src/` **do not `print`** step-by-step traces (unlike the teaching
  cells of the lessons). They return data (e.g. `(value, chosen_sites, table)` as in Lesson 12)
  and the notebook prints and plots it.

**Tests (the course has none: keep them minimal and readable)**
- Plain `assert` and `pytest.raises(ValueError)`, replacing the course's `try/except` +
  `print("Expected error:", error)` pattern (Lesson 08 section 4; Lesson 03 Cell 05).
- Each test has a one-line comment saying what it proves.

**Beyond the course (new for the team — comment them extra carefully):** Greedy and its
exchange-argument justification, `heapq`, Dijkstra, and `pytest`.

---

## 6. Repository layout and ownership

```
CP4-Dynamic/
├── README.md                     shared (Q1 section: Thomas; Q2 section: Marco)
├── requirements.txt              shared (every dependency justified)
├── pytest.ini                    shared
├── .gitignore                    shared
├── claude/
│   └── SPEC.md                   this document
├── data/
│   ├── problema1.csv             Q1 nodes (Step 2)
│   ├── problema1_edges.csv       Q1 roads (Step 2)
│   └── problema2.csv             Q2
├── src/
│   ├── __init__.py
│   ├── estruturas.py             shared: Q1 block (Step 2) + Q2 block
│   ├── data_generator.py         Q1 (Step 2)
│   ├── data_loader.py            Q1 (Step 2)
│   ├── shortest_paths.py         Q1 (Step 2)
│   ├── objective.py              Q1 (Steps 2–3)
│   ├── greedy.py                 Q1 (Step 3)
│   ├── dynamic_programming.py    Q1 (Step 4)
│   ├── plots.py                  Q1 (Step 6)
│   ├── measurements.py           Q1 (Step 7)
│   ├── brute_force.py            Q2 (do not touch)
│   └── divide_conquer.py         Q2 (do not touch)
├── notebooks/
│   ├── questao1.ipynb            Q1 (Step 8)
│   └── questao2.ipynb            Q2
├── figures/
│   ├── questao1/                 Q1 (generated by code)
│   └── questao2/                 Q2
├── tests/
│   ├── test_questao1.py          Q1 (single file)
│   └── test_questao2.py          Q2
└── docs/
    └── analise_complexidade.md   shared (Q1 section: Step 7)
```

Shared files (`README.md`, `requirements.txt`, `estruturas.py`, `analise_complexidade.md`) are
edited in a **coordinated** way: each person only adds to their own section or block and pulls
before editing. Step 1 creates only the modules that Step 1 lists; the other Q1 modules are
created in the step that first needs them (D13).

---

## 7. Step plan

| Step | Content | Assignment part | Status |
|---|---|---|---|
| 1 | Repository skeleton, tooling, README skeleton | structure | **specified in Section 8** |
| 2 | Data model, generator (SEED = 1), loader, Dijkstra, order `π` | A | **specified in Section 9** |
| 3 | `Solution`, `J(S)`, marginal cost, `λ` calibration, Greedy | B | decisions D11–D12; details TBD |
| 4 | DP formulation, implementation, reconstruction | C | model in Section 4; details TBD |
| 5 | Greedy × DP comparison and hand-built counterexample | D | TBD |
| 6 | Service sequence and the 3 figures | E | TBD |
| 7 | Complexity analysis and measurements | F | TBD |
| 8 | Notebook, remaining tests, README final answer | delivery | TBD |

---

## 8. STEP 1 — Repository skeleton

**Goal:** make the repository ready for progressive development. No algorithm code.

### 8.1 Tasks

1. **Audit** the existing repository (`data/`, `docs/`, `notebooks/`, `src/`, `tests/`,
   `README.md`, `requirements.txt`). List what is missing versus Section 6. Keep everything
   that already exists.
2. **Create the missing Question 1 items only:**
   - `src/__init__.py` (empty file with a one-line module docstring is fine).
   - `src/estruturas.py`, `src/greedy.py`, `src/dynamic_programming.py`: each with **only a
     module docstring** stating its responsibility (per Section 6) and no code. Skip any that
     already exist with content.
   - `tests/test_questao1.py`: a single smoke test that imports the three modules above and
     asserts nothing else, with a one-line comment saying what it proves (Section 5.2).
   - `notebooks/questao1.ipynb`: valid nbformat 4 notebook with (a) a markdown title cell and
     (b) one code cell that adds the repository root to `sys.path` and imports `src`.
     It must execute end to end with no errors.
   - `figures/questao1/.gitkeep` (create `figures/` if absent; do not create `questao2/`
     content, but if `figures/questao2/` is absent create only its `.gitkeep`).
   - `docs/analise_complexidade.md`: only a title and an empty `## Question 1` heading, if
     the file does not exist.
3. **`pytest.ini`:** `pythonpath = .` and `testpaths = tests`.
4. **`.gitignore`:** Python bytecode, `.pytest_cache/`, virtualenvs, `.ipynb_checkpoints/`,
   OS files. **Do not ignore** `figures/` or `data/`.
5. **`requirements.txt`** (append only what is missing; one justification comment per line):
   - `matplotlib` — figure generation (allowed: plotting).
   - `pytest` — automated tests (allowed: testing).
   - `jupyter` — run the executable notebooks.
   Use compatible-release specifiers (`~=`) matching the versions installed at creation time.
6. **`README.md` skeleton** (English). If a README already exists, extend it without deleting
   content. Structure:
   - Title, one-line description.
   - **Team** table (Name | RM) with the 5 members from Section 2.
   - **Reproducibility:** `SEED = 1`.
   - `# Question 1 — Emergency Logistics` with the 8 required subsections as empty headings
     containing `_TODO_`: 1 Problem, 2 Adopted model, 3 Data structures, 4 Algorithms,
     5 How to run, 6 Results, 7 Complexity, 8 Limitations.
   - `# Question 2 — Energy Consumption Management` with the same 8 headings and `_TODO_`,
     and a note "Owner: Marco Aurélio" (do not fill it).
   - Final section `## Final question (max 300 words)` with the question text from the
     assignment and `_TODO_`.

### 8.2 Acceptance criteria

- `pytest` runs from the repository root and passes (the smoke test).
- The notebook runs top to bottom (`jupyter nbconvert --to notebook --execute`) without errors.
- No file outside the list above was modified or created; no Q2 content was filled.
- `git status` shows only additions/modifications the team can review; **no commits were made**.
- `README.md` contains all 5 names with their RMs exactly as in Section 2 and `SEED = 1`.

### 8.3 Out of scope for Step 1

Graph, Dijkstra, data generation, CSV contents, Greedy, DP, figures, complexity text, any
Question 2 work.

---

## 9. STEP 2 — Data model, generator, loader, Dijkstra, order `π` (Part A)

**Goal:** build the Question 1 dataset from `SEED = 1`, load it back with validation, and
compute shortest distances and the canonical order `π`. **No objective function, no Greedy,
no DP, no plots.**

### 9.1 Generator parameters (constants at the top of `src/data_generator.py`)

```python
SEED = 1                          # the ONLY place where the seed is defined
N_SITES = 20
GRID_SIZE = 100                   # integer coordinates in [0, GRID_SIZE]
DEPOT_POSITION = (50, 50)
NEAREST_NEIGHBORS = 3             # every node is linked to its 3 nearest nodes
TARGET_AVAILABLE_ROADS = 38       # the assignment requires >= 35 connections
TARGET_BLOCKED_ROADS = 8          # at least 6 are guaranteed
DETOUR_RANGE = (1.0, 1.3)         # distance = max(1, round(euclidean * U(detour)))
PEOPLE_RANGE = (80, 1500)
PRIORITY_RANGE = (1, 5)
DEMAND_RATES_PER_100_PEOPLE = {   # fixed resource order: water, medicine, food, hygiene_kits, blankets
    "water": 3, "medicine": 1, "food": 3, "hygiene_kits": 2, "blankets": 2,
}
DEMAND_NOISE = (0.8, 1.2)         # each demand = max(1, round(people/100 * rate * U(noise)))
BENEFIT_FRACTION_RANGE = (0.6, 1.0)   # expected_benefit = round(people * U(range))
CAPACITY_FRACTION = 0.35          # default capacity = floor(fraction * total load); NOT in the CSV
```

**Algorithm** (all randomness comes from **one** `random.Random(SEED)` created inside
`generate_instance`; the order of draws below is part of the contract and must be documented in
the docstring):

1. Site coordinates, in site-id order (`1..N_SITES`): draw `x` then `y`; redraw on collision
   with an existing node position. The depot is fixed at `DEPOT_POSITION` (node id `0`).
2. Candidate roads: the union of the `NEAREST_NEIGHBORS` nearest nodes of every node (ties broken
   by node id). Then, while the number of roads is below
   `TARGET_AVAILABLE_ROADS + TARGET_BLOCKED_ROADS`, add a random pair not yet present.
   If the nearest-neighbor union already exceeds that total, keep all of it.
3. Road distances, iterating the pairs in sorted `(node_a, node_b)` order with `node_a < node_b`.
4. Blocked roads: take the sorted pairs, shuffle with the same RNG, and mark a road as blocked
   only if **every node stays reachable from the depot** through the remaining available roads;
   stop at `TARGET_BLOCKED_ROADS`. If that many cannot be blocked, raise `RuntimeError`.
5. Site attributes, in site-id order: `people_affected`, `priority`, the five demand noises in
   the fixed resource order, then the benefit fraction.

**Guarantees** (also checked by tests): 1 depot + 20 sites; at least 35 available roads and at
least 6 blocked roads; fewer roads than a complete graph (`V(V−1)/2`); the graph of available
roads is connected; every site has `load > 0`; all values are integers.

### 9.2 Files and public API

**`src/estruturas.py`** — inside the `# ===== Question 1 =====` block:
- `Graph = dict[int, list[tuple[int, int]]]` (adjacency list: node → list of `(neighbor, distance)`).
- `@dataclass(frozen=True, slots=True) Depot`: `node_id`, `name`, `x`, `y`.
- `@dataclass(frozen=True, slots=True) Site`: `node_id`, `name`, `x`, `y`, `people_affected`,
  `priority`, `water`, `medicine`, `food`, `hygiene_kits`, `blankets`, `expected_benefit`;
  validation in `__post_init__` (`priority` in `1..5`, non-negative integers, `load > 0`);
  properties `load` (sum of the five demands) and `effective_benefit`
  (`expected_benefit * priority`).
- `@dataclass(frozen=True, slots=True) Edge`: `node_a`, `node_b`, `distance`, `available`
  (`node_a < node_b`, `distance > 0`).
- `Instance` (frozen dataclass): `depot`, `sites` (tuple), `edges` (tuple); method `graph()`
  returning the adjacency of the **available** edges only; helper to look a site up by id.
- **`Solution` is NOT created in this step.**

**`src/data_generator.py`**
- `generate_instance(seed: int = SEED) -> Instance`
- `write_instance(instance, nodes_path, edges_path) -> None` — deterministic output (rows
  sorted by id / by `(node_a, node_b)`, `\n` line endings).
- `python -m src.data_generator` writes `data/problema1.csv` and `data/problema1_edges.csv`
  (paths derived from the repository root, not from the current directory).

**`src/data_loader.py`**
- `load_instance(nodes_path, edges_path) -> Instance` using the standard `csv` module.
- Raises `ValueError` with a clear message for: missing file or column, non-integer value,
  duplicated node id, not exactly one `depot` row (which must have id `0`), unknown `kind`,
  an edge that references an unknown node, `node_a >= node_b`, duplicated edge, `distance <= 0`,
  `available` not in `{0, 1}`, `priority` outside `1..5`, negative demand, `load == 0`.

**CSV schema**
- `data/problema1.csv` columns, in this order: `node_id, name, kind, x, y, people_affected,
  priority, water, medicine, food, hygiene_kits, blankets, expected_benefit`.
  `kind` is `depot` or `site`; the depot row has `0` in every attribute column.
  Names: `Distribution Center` for the depot, `Site 01` … `Site 20` for the sites.
- `data/problema1_edges.csv` columns: `node_a, node_b, distance, available` (`1` = usable,
  `0` = blocked). One row per (undirected) road; blocked roads stay in the file.

**`src/shortest_paths.py`**
- `dijkstra(graph, source) -> tuple[dict[int, float], dict[int, int | None]]` — distances
  (`math.inf` when unreachable) and parent map. Uses `heapq` with **lazy deletion** (skip stale
  heap entries); heap items are `(distance, node_id)`; a neighbor is updated only when the new
  distance is **strictly** smaller, so ties are deterministic. Raises `ValueError` for an unknown
  source or a non-positive weight.
- `reconstruct_path(parent, source, target) -> list[int] | None`.
- `distance_matrix(graph, sources) -> dict[int, dict[int, float]]` — one Dijkstra per source.
- Each function carries `# TIME:` / `# MEMORY:` comments in terms of `V` and `E`
  (`O((V + E) log V)` per source, with the heap holding up to `E` entries).

**`src/objective.py`** (only `π` in this step)
- `build_order(distance, parent, depot_id) -> list[int]` — pre-order DFS of the tree defined
  by `parent`, children sorted by `(distance[child], child)`, depot excluded, unreachable nodes
  excluded. Recursive, as in the course DFS notebook; document its depth (`O(V)` worst case).

### 9.3 Tests to add to `tests/test_questao1.py`

Deterministic; each test has a one-line comment saying what it proves.
- Generator: same seed gives an identical `Instance`; a different seed gives a different one;
  the guarantees of Section 9.1 hold for `SEED = 1`; `data_generator.SEED == 1`.
- Formulas: `Site.load` and `Site.effective_benefit` on a hand-built site.
- Loader: `write_instance` followed by `load_instance` reproduces the instance; each invalid
  input listed in Section 9.2 raises `ValueError` (use `pytest.raises`).
- Dijkstra on a **hand-built** graph with known answers: a blocked road forces a detour (the
  detour distance is asserted), an unreachable node gets `math.inf`, `reconstruct_path` returns
  the expected path, an unknown source raises `ValueError`.
- `build_order` on a hand-built tree: expected pre-order, tie-break by node id, unreachable
  node excluded, depot absent.

### 9.4 Acceptance criteria

- `pytest` passes from the repository root.
- `python -m src.data_generator` run twice produces byte-identical CSV files, and
  `load_instance` reads them back without error.
- No `networkx`; the only new imports are from the standard library (`csv`, `heapq`, `math`,
  `random`, `dataclasses`, `pathlib`, `collections`).
- No `print` in library code; docstrings and `# TIME:` / `# MEMORY:` comments follow
  Section 5.2.
- Nothing from Steps 3+ exists (no `Solution`, `J(S)`, Greedy, DP, plots, measurements).
- No Question 2 file was touched; no commits were made.

### 9.5 Out of scope for Step 2

`Solution`, route length, `J(S)`, marginal cost, `λ`, Greedy, DP, figures, README text,
complexity write-up, any Question 2 work.

---

## 10. Remaining open decisions (do not implement until decided)

1. Numeric value of `λ` (rule fixed in D11) — Step 3, after the real dataset exists.
2. `Solution` fields and the exact signatures of `J(S)` and the marginal cost — Step 3.
3. DP implementation details (tables returned, tie handling in reconstruction) — Step 4.
4. The hand-built counterexample instance — Step 5.
5. Figure layouts — Step 6.
6. Record the Python version used in the README (random-number streams are guaranteed
   reproducible only for the same Python version) — Step 8.
