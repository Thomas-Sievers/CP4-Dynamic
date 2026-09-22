"""Question 1: Dynamic Programming solver.

Implements ``solve_dp``, a bottom-up DP over states ``(last site, load)``
that finds the combination of service points maximizing the shared
objective ``J(S)`` within vehicle capacity, plus reconstruction of the
chosen set from the stored predecessor table.

DP explanation (Section 4 / Part C checklist)
----------------------------------------------
* **State**: ``dp[i][c]`` = best ``J`` over routes, in pi order, that end
  at ``pi_order[i]`` and use total load exactly ``c``.
* **Decision**: for the route ending at ``pi_order[i]``, which earlier
  site ``pi_order[j]`` (``j < i``) directly precedes it -- or whether
  ``pi_order[i]`` is the first site of the route (predecessor: the depot).
* **Base case**: ``dp[i][w_i] = b_i - lambda * d(depot, pi_order[i])``,
  i.e. ``pi_order[i]`` is the only site chosen so far.
* **Recurrence**: for ``c > w_i``,
  ``dp[i][c] = b_i + max_{j<i, dp[j][c-w_i] defined} (dp[j][c-w_i] - lambda * d(pi_order[j], pi_order[i]))``.
* **Repeated states**: many different subsets S can end at the same
  ``(i, c)`` pair; the table stores only the best one, which is exactly
  what makes the DP polynomial instead of exponential.
* **Safe fill order**: rows are filled in increasing ``i`` (pi order);
  row ``i`` only reads rows ``j < i``, so by the time row ``i`` is
  computed every row it depends on is already final.
* **Reconstruction**: the predecessor of the argmax cell is stored per
  cell; walking those pointers back to a base case (sentinel ``-1``)
  recovers the selected sites, which are then reversed into pi order.

Bottom-up vs. top-down (Lesson 09): bottom-up is used here because it
avoids a recursion stack (up to ``O(N)`` deep, harmless at N=20 but not a
pattern to rely on), fills the table in one pass with a safe order that
is easy to state (see above), and the filled table is exactly Figure 3 --
a top-down/memoized version would only build the states it visits, which
is fine for the answer but leaves an incomplete table to plot.
"""

from __future__ import annotations

from src.estruturas import Instance, Solution
from src.objective import LAMBDA_DISTANCE_PRICE, objective_value, route_length

UNREACHABLE = float("-inf")  # sentinel: no route achieves this (site, load) state


def solve_dp(
    instance: Instance,
    capacity: int,
    pi_order: list[int],
    distance: dict[int, dict[int, float]],
    lambda_price: int = LAMBDA_DISTANCE_PRICE,
) -> tuple[Solution, list[list[float]]]:
    """Find the combination of sites maximizing J(S) within capacity, by DP.

    Ties in the recurrence keep the first candidate found: the base case
    (site is first) is tried before any predecessor, and predecessors are
    tried in ascending pi order (``j = 0, 1, ...``) with a strict ``>``
    comparison -- so on an exact tie, the earliest-found option wins.

    Parameters
    ----------
    instance : Instance
        The dataset (depot + sites).
    capacity : int
        Maximum total load the route may carry; must be non-negative.
    pi_order : list[int]
        Candidate site ids in the canonical order pi (D9), depot excluded.
    distance : dict[int, dict[int, float]]
        Pairwise shortest distances, as returned by
        ``shortest_paths.distance_matrix`` over depot + pi_order.
    lambda_price : int
        Distance price (D11); defaults to the calibrated constant.

    Returns
    -------
    tuple[Solution, list[list[float]]]
        The optimal plan (same shape as ``greedy.solve_greedy``'s result)
        and the filled ``dp`` table (``dp[i][c]``, ``UNREACHABLE`` where
        no route reaches that state) for Figure 3.

    Raises
    ------
    ValueError
        If capacity is negative or lambda_price is not positive.
    """
    if capacity < 0:
        raise ValueError(f"capacity must be non-negative, got {capacity}.")
    if lambda_price <= 0:
        raise ValueError(f"lambda_price must be positive, got {lambda_price}.")

    depot_id = instance.depot.node_id
    benefit = {site.node_id: site.effective_benefit for site in instance.sites}
    load = {site.node_id: site.load for site in instance.sites}

    n_candidates = len(pi_order)
    dp = [[UNREACHABLE] * (capacity + 1) for _ in range(n_candidates)]
    predecessor: list[list[int | None]] = [[None] * (capacity + 1) for _ in range(n_candidates)]

    # TIME: N candidates x up to (C+1) loads x up to N predecessors each
    # -> O(N^2 * C).
    # MEMORY: dp and predecessor are both N x (C+1) -> O(N * C).
    for i in range(n_candidates):
        site_i = pi_order[i]
        site_load = load[site_i]
        if site_load > capacity:
            continue  # site_i alone would already exceed capacity: unreachable at every c

        for c in range(site_load, capacity + 1):
            best_value = UNREACHABLE
            best_predecessor: int | None = None

            if c == site_load:
                # Base case: site_i is the first (and so far only) site of the route.
                best_value = benefit[site_i] - lambda_price * distance[depot_id][site_i]
                best_predecessor = -1  # sentinel: predecessor is the depot

            remaining_load = c - site_load
            for j in range(i):
                if dp[j][remaining_load] == UNREACHABLE:
                    continue
                candidate_value = (
                    dp[j][remaining_load] + benefit[site_i] - lambda_price * distance[pi_order[j]][site_i]
                )
                if candidate_value > best_value:
                    best_value = candidate_value
                    best_predecessor = j

            dp[i][c] = best_value
            predecessor[i][c] = best_predecessor

    best_cell = _find_best_cell(dp)
    selected = _reconstruct_selected_sites(predecessor, pi_order, load, best_cell)

    solution = Solution(
        selected_sites=tuple(selected),
        total_benefit=sum(benefit[site] for site in selected),
        total_load=sum(load[site] for site in selected),
        route_length=route_length(selected, depot_id, distance),
        objective_value=objective_value(selected, depot_id, distance, benefit, lambda_price),
    )
    return solution, dp


def _find_best_cell(dp: list[list[float]]) -> tuple[int, int] | None:
    """Find the (i, c) cell with the largest dp value, or None if none beats the empty set.

    Section 4's answer is ``max(0, max_{i,c} dp[i][c])``: the empty set
    (value 0) is always an option, so a cell is only reported if it beats it.
    """
    best_value = 0.0
    best_cell: tuple[int, int] | None = None
    for i, row in enumerate(dp):
        for c, value in enumerate(row):
            if value > best_value:
                best_value = value
                best_cell = (i, c)
    return best_cell


def _reconstruct_selected_sites(
    predecessor: list[list[int | None]],
    pi_order: list[int],
    load: dict[int, int],
    best_cell: tuple[int, int] | None,
) -> list[int]:
    """Walk the predecessor pointers back from best_cell to the site ids, in pi order."""
    # Base case: no cell beat the empty set, so nothing is selected.
    if best_cell is None:
        return []

    positions: list[int] = []
    i, c = best_cell
    while True:
        positions.append(i)
        predecessor_position = predecessor[i][c]
        if predecessor_position == -1:
            break
        c -= load[pi_order[i]]
        i = predecessor_position

    positions.reverse()
    return [pi_order[position] for position in positions]
