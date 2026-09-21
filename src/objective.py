"""Question 1: canonical visiting order pi, route length, objective and marginal cost.

Step 2 added ``build_order`` (Decision D9). Step 3 adds the route length
``L(S)``, the shared objective ``J(S)`` (Section 4), the marginal
insertion cost ``delta_J_i(S)`` used by Greedy (Decision D12), and the
``lambda`` calibration rule (Decision D11).
"""

from __future__ import annotations

import statistics


def build_order(distance: dict[int, float], parent: dict[int, int | None], depot_id: int) -> list[int]:
    """Pre-order DFS of the Dijkstra shortest-path tree, starting at the depot.

    Decision D9: children of a node are visited in ``(distance, node_id)``
    order, so nodes in the same branch of the tree stay consecutive in
    ``pi`` -- a compact cluster of sites ends up cheap to visit in
    sequence. The depot itself is excluded from the returned order;
    nodes unreachable from the depot (``distance == math.inf``, no
    parent) are excluded too, since they never appear as anyone's child.

    Parameters
    ----------
    distance : dict[int, float]
        Distances from the depot, as returned by ``shortest_paths.dijkstra``.
    parent : dict[int, int | None]
        Predecessor map, as returned by ``shortest_paths.dijkstra``.
    depot_id : int
        Node id of the depot (root of the tree).

    Returns
    -------
    list[int]
        Node ids in pre-order DFS order, depot excluded.
    """
    # TIME: building the children map and running the DFS each visit every
    # reachable node and tree edge once -> O(V); sorting every node's
    # children by (distance, id) costs O(V log V) overall.
    # MEMORY: the children map and the order list are O(V); recursion
    # depth equals the tree height, up to O(V) in the worst case (a
    # single chain) -- see Decision D9.
    children: dict[int, list[int]] = {node: [] for node in parent}
    for node, node_parent in parent.items():
        if node_parent is not None:
            children[node_parent].append(node)
    for node_children in children.values():
        node_children.sort(key=lambda child: (distance[child], child))

    order: list[int] = []

    def _visit(node: int) -> None:
        # Base case: a leaf has no children, so nothing more is appended.
        for child in children.get(node, []):
            order.append(child)
            _visit(child)

    _visit(depot_id)
    return order


# Decision D11: lambda is a fixed positive integer constant, calibrated
# once from the seed-1 dataset with calibrate_lambda (median effective
# benefit / median distance from the depot, rounded), then hardcoded here
# -- it is never recomputed at run time. See docs/analise_complexidade.md
# for the derivation; a sensitivity sweep over lambda is a Part D figure.
LAMBDA_DISTANCE_PRICE = 21


def calibrate_lambda(effective_benefits: list[int], distances_from_depot: list[float]) -> int:
    """Suggest a value for lambda from D11's rule (run once, then hardcode the result).

    Parameters
    ----------
    effective_benefits : list[int]
        effective_benefit of every candidate site.
    distances_from_depot : list[float]
        Shortest distance from the depot to every candidate site.

    Returns
    -------
    int
        round(median(effective_benefits) / median(distances_from_depot)).

    Raises
    ------
    ValueError
        If either list is empty or the median distance is not positive.
    """
    if not effective_benefits or not distances_from_depot:
        raise ValueError("Need at least one site to calibrate lambda.")
    median_distance = statistics.median(distances_from_depot)
    if median_distance <= 0:
        raise ValueError(f"Median distance from the depot must be positive, got {median_distance}.")
    return round(statistics.median(effective_benefits) / median_distance)


def route_length(order: list[int], depot_id: int, distance: dict[int, dict[int, float]]) -> int:
    """L(S): length of the open route depot -> order[0] -> ... -> order[-1].

    Parameters
    ----------
    order : list[int]
        Site ids of S, already sorted in pi order.
    depot_id : int
        Node id of the depot.
    distance : dict[int, dict[int, float]]
        Pairwise shortest distances, as returned by ``shortest_paths.distance_matrix``.

    Returns
    -------
    int
        L(S); 0 for an empty route.
    """
    # Base case: nothing to visit, no distance is traveled.
    if not order:
        return 0

    total = distance[depot_id][order[0]]
    for previous_site, current_site in zip(order, order[1:]):
        total += distance[previous_site][current_site]
    return int(total)


def objective_value(
    order: list[int],
    depot_id: int,
    distance: dict[int, dict[int, float]],
    benefit: dict[int, int],
    lambda_price: int,
) -> int:
    """J(S) = sum of benefits over S minus lambda times the route length L(S).

    The capacity constraint (sum of loads <= C) is checked by the caller,
    not here: J is defined for any set S (Section 4).

    Parameters
    ----------
    order : list[int]
        Site ids of S, already sorted in pi order.
    depot_id : int
        Node id of the depot.
    distance : dict[int, dict[int, float]]
        Pairwise shortest distances.
    benefit : dict[int, int]
        effective_benefit of every candidate site, keyed by node_id.
    lambda_price : int
        Distance price (Decision D11).

    Returns
    -------
    int
        J(S). J(empty set) == 0.
    """
    total_benefit = sum(benefit[site] for site in order)
    return total_benefit - lambda_price * route_length(order, depot_id, distance)


def _pi_neighbors(candidate: int, selected: list[int], pi_rank: dict[int, int], depot_id: int) -> tuple[int, int | None]:
    """Find candidate's pi-predecessor and pi-successor if inserted into selected.

    Parameters
    ----------
    candidate : int
        Site id not currently in selected.
    selected : list[int]
        Current S, already sorted in pi order.
    pi_rank : dict[int, int]
        node_id -> position in the global order pi.
    depot_id : int
        Node id of the depot, used as the predecessor when candidate would be first.

    Returns
    -------
    tuple[int, int | None]
        (predecessor, successor); successor is None when candidate would be last.
    """
    candidate_rank = pi_rank[candidate]
    predecessor = depot_id
    # Base case: selected is empty, candidate would be the only (first) site.
    for site in selected:
        if pi_rank[site] < candidate_rank:
            predecessor = site
        else:
            return predecessor, site
    return predecessor, None


def marginal_gain(
    candidate: int,
    selected: list[int],
    pi_rank: dict[int, int],
    depot_id: int,
    distance: dict[int, dict[int, float]],
    benefit: dict[int, int],
    lambda_price: int,
) -> int:
    """delta_J_candidate(S): the exact change in J from inserting candidate into S at its pi position.

    Section 4: if p is the pi-predecessor of candidate in S (or the depot)
    and s its pi-successor (or none), the extra route length is
    ``d(p, candidate) + d(candidate, s) - d(p, s)`` (or just ``d(p,
    candidate)`` if candidate would be last); the marginal gain is the
    candidate's benefit minus lambda times that extra length.

    Parameters
    ----------
    candidate : int
        Site id not currently in selected.
    selected : list[int]
        Current S, already sorted in pi order.
    pi_rank : dict[int, int]
        node_id -> position in the global order pi.
    depot_id : int
        Node id of the depot.
    distance : dict[int, dict[int, float]]
        Pairwise shortest distances.
    benefit : dict[int, int]
        effective_benefit of every candidate site, keyed by node_id.
    lambda_price : int
        Distance price (Decision D11).

    Returns
    -------
    int
        delta_J_candidate(S) = J(S union {candidate}) - J(S).
    """
    predecessor, successor = _pi_neighbors(candidate, selected, pi_rank, depot_id)
    if successor is None:
        extra_length = distance[predecessor][candidate]
    else:
        extra_length = (
            distance[predecessor][candidate]
            + distance[candidate][successor]
            - distance[predecessor][successor]
        )
    return benefit[candidate] - lambda_price * round(extra_length)
