"""Question 1: Greedy solver.

Implements ``solve_greedy``, which builds a service plan by repeatedly
picking the not-yet-chosen site with the highest marginal-benefit density
under the shared objective ``J(S)`` (decision D12), until no eligible site
remains or capacity is exhausted.
"""

from __future__ import annotations

from src.estruturas import Instance, Solution
from src.objective import LAMBDA_DISTANCE_PRICE, marginal_gain, objective_value, route_length


def solve_greedy(
    instance: Instance,
    capacity: int,
    pi_order: list[int],
    distance: dict[int, dict[int, float]],
    lambda_price: int = LAMBDA_DISTANCE_PRICE,
) -> Solution:
    """Build a service plan with the D12 greedy rule: best benefit density first.

    At each step, every not-yet-selected candidate site that still fits
    the remaining capacity gets its marginal gain ``delta_J_i(S)``
    (``objective.marginal_gain``) and a score ``delta_J_i(S) / load_i``.
    Only candidates with ``delta_J_i(S) > 0`` are eligible. The eligible
    site with the highest score is picked; ties break by larger
    ``delta_J_i(S)``, then smaller load, then smaller node_id. The loop
    stops when no eligible candidate remains.

    Parameters
    ----------
    instance : Instance
        The dataset (depot + sites).
    capacity : int
        Maximum total load the route may carry; must be non-negative.
    pi_order : list[int]
        Candidate site ids in the canonical order pi (D9), depot excluded
        (only sites reachable from the depot may appear here, per D6).
    distance : dict[int, dict[int, float]]
        Pairwise shortest distances, as returned by
        ``shortest_paths.distance_matrix`` over depot + pi_order.
    lambda_price : int
        Distance price (D11); defaults to the calibrated constant.

    Returns
    -------
    Solution
        The greedy plan: selected sites in pi order, its totals, and J(S).

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
    pi_rank = {node_id: rank for rank, node_id in enumerate(pi_order)}
    benefit = {site.node_id: site.effective_benefit for site in instance.sites}
    load = {site.node_id: site.load for site in instance.sites}

    selected: list[int] = []
    remaining_capacity = capacity
    remaining_candidates = set(pi_order)

    # TIME: up to N rounds, each scanning up to N remaining candidates and
    # doing an O(N) marginal-gain lookup + an O(N) sorted insertion ->
    # O(N^3) worst case here (N <= 20, so this is fast in practice); a
    # sparser implementation would trade simplicity for speed.
    # MEMORY: pi_rank, benefit, load and selected are all O(N).
    while True:
        best_site: int | None = None
        best_gain = 0
        best_score = 0.0

        # Scanning by ascending node_id makes "keep the first candidate
        # found" equivalent to the "smaller node_id" tie-break rule.
        for candidate in sorted(remaining_candidates):
            if load[candidate] > remaining_capacity:
                continue
            gain = marginal_gain(candidate, selected, pi_rank, depot_id, distance, benefit, lambda_price)
            if gain <= 0:
                continue
            score = gain / load[candidate]

            if best_site is None:
                best_site, best_gain, best_score = candidate, gain, score
            elif score > best_score:
                best_site, best_gain, best_score = candidate, gain, score
            elif score == best_score and gain > best_gain:
                best_site, best_gain, best_score = candidate, gain, score
            elif score == best_score and gain == best_gain and load[candidate] < load[best_site]:
                best_site, best_gain, best_score = candidate, gain, score

        if best_site is None:
            break

        _insert_in_pi_order(selected, best_site, pi_rank)
        remaining_candidates.discard(best_site)
        remaining_capacity -= load[best_site]

    total_benefit = sum(benefit[site] for site in selected)
    total_load = sum(load[site] for site in selected)
    return Solution(
        selected_sites=tuple(selected),
        total_benefit=total_benefit,
        total_load=total_load,
        route_length=route_length(selected, depot_id, distance),
        objective_value=objective_value(selected, depot_id, distance, benefit, lambda_price),
    )


def _insert_in_pi_order(selected: list[int], candidate: int, pi_rank: dict[int, int]) -> None:
    """Insert candidate into selected in place, keeping it sorted by pi rank."""
    position = 0
    # Base case: candidate's rank is smaller than everyone already in
    # selected, so it is inserted at position 0.
    while position < len(selected) and pi_rank[selected[position]] < pi_rank[candidate]:
        position += 1
    selected.insert(position, candidate)
