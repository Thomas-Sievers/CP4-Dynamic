"""Question 1: deterministic dataset generation, seeded by ``SEED``.

Writes ``data/problema1.csv`` (nodes) and ``data/problema1_edges.csv``
(roads) when run as ``python -m src.data_generator``.
"""

from __future__ import annotations

import csv
import math
import random
from collections import deque
from pathlib import Path

from src.estruturas import Depot, Edge, Instance, Site

SEED = 1  # the ONLY place where the seed is defined (Section 2 of the spec)

N_SITES = 20
GRID_SIZE = 100  # integer coordinates in [0, GRID_SIZE]
DEPOT_POSITION = (50, 50)
NEAREST_NEIGHBORS = 3  # every node is linked to its 3 nearest nodes
TARGET_AVAILABLE_ROADS = 38  # the assignment requires >= 35 connections
TARGET_BLOCKED_ROADS = 8  # at least 6 are guaranteed
DETOUR_RANGE = (1.0, 1.3)  # distance = max(1, round(euclidean * U(detour)))
PEOPLE_RANGE = (80, 1500)
PRIORITY_RANGE = (1, 5)
DEMAND_RATES_PER_100_PEOPLE = {  # fixed resource order: water, medicine, food, hygiene_kits, blankets
    "water": 3,
    "medicine": 1,
    "food": 3,
    "hygiene_kits": 2,
    "blankets": 2,
}
DEMAND_NOISE = (0.8, 1.2)  # each demand = max(1, round(people/100 * rate * U(noise)))
BENEFIT_FRACTION_RANGE = (0.6, 1.0)  # expected_benefit = round(people * U(range))
CAPACITY_FRACTION = 0.35  # default capacity = floor(fraction * total load); NOT in the CSV

NODE_COLUMNS = (
    "node_id", "name", "kind", "x", "y", "people_affected", "priority",
    "water", "medicine", "food", "hygiene_kits", "blankets", "expected_benefit",
)
EDGE_COLUMNS = ("node_a", "node_b", "distance", "available")

_RESOURCE_ORDER = ("water", "medicine", "food", "hygiene_kits", "blankets")


def generate_instance(seed: int = SEED) -> Instance:
    """Generate a deterministic Question 1 instance.

    All randomness comes from a single ``random.Random(seed)`` created
    here; the draws happen in this fixed order (part of the reproducibility
    contract, do not reorder):

    1. Site coordinates, in site-id order (redraw on collision).
    2. Candidate roads: union of each node's ``NEAREST_NEIGHBORS`` nearest
       neighbors, then random pairs until the available+blocked target is met.
    3. Road distances, iterating the candidate pairs in sorted order.
    4. Blocked roads: shuffle the sorted pairs and block while every node
       stays reachable from the depot, up to ``TARGET_BLOCKED_ROADS``.
    5. Site attributes, in site-id order (people, priority, the five
       demand noises in a fixed order, then the benefit fraction).

    Parameters
    ----------
    seed : int
        Seed for the random number generator.

    Returns
    -------
    Instance
        The generated depot, sites and edges.

    Raises
    ------
    RuntimeError
        If fewer than ``TARGET_BLOCKED_ROADS`` roads can be blocked while
        keeping every node reachable from the depot.
    """
    rng = random.Random(seed)

    depot = Depot(node_id=0, name="Distribution Center", x=DEPOT_POSITION[0], y=DEPOT_POSITION[1])

    # Step 1: site coordinates.
    positions: dict[int, tuple[int, int]] = {0: DEPOT_POSITION}
    occupied_positions = {DEPOT_POSITION}
    for site_id in range(1, N_SITES + 1):
        while True:
            x = rng.randint(0, GRID_SIZE)
            y = rng.randint(0, GRID_SIZE)
            if (x, y) not in occupied_positions:
                positions[site_id] = (x, y)
                occupied_positions.add((x, y))
                break

    all_node_ids = list(positions.keys())

    # Step 2: candidate roads -- nearest-neighbor union, then random fill.
    candidate_roads: set[tuple[int, int]] = set()
    for node in all_node_ids:
        neighbor_distances = sorted(
            (
                (_euclidean(positions[node], positions[other]), other)
                for other in all_node_ids
                if other != node
            ),
            key=lambda item: (item[0], item[1]),
        )
        for _, neighbor in neighbor_distances[:NEAREST_NEIGHBORS]:
            candidate_roads.add((min(node, neighbor), max(node, neighbor)))

    target_total = TARGET_AVAILABLE_ROADS + TARGET_BLOCKED_ROADS
    while len(candidate_roads) < target_total:
        a = rng.randint(0, N_SITES)
        b = rng.randint(0, N_SITES)
        if a == b:
            continue
        candidate_roads.add((min(a, b), max(a, b)))

    # Step 3: road distances, sorted pair order.
    sorted_pairs = sorted(candidate_roads)
    distance_by_pair: dict[tuple[int, int], int] = {}
    for node_a, node_b in sorted_pairs:
        euclidean = _euclidean(positions[node_a], positions[node_b])
        detour = rng.uniform(*DETOUR_RANGE)
        distance_by_pair[(node_a, node_b)] = max(1, round(euclidean * detour))

    # Step 4: block roads while every node stays reachable from the depot.
    shuffled_pairs = list(sorted_pairs)
    rng.shuffle(shuffled_pairs)
    blocked_pairs: set[tuple[int, int]] = set()
    for pair in shuffled_pairs:
        if len(blocked_pairs) >= TARGET_BLOCKED_ROADS:
            break
        if _all_reachable(all_node_ids, sorted_pairs, blocked_pairs | {pair}):
            blocked_pairs.add(pair)
    if len(blocked_pairs) < TARGET_BLOCKED_ROADS:
        raise RuntimeError(
            f"Could not block {TARGET_BLOCKED_ROADS} roads while keeping every "
            f"node reachable from the depot; only {len(blocked_pairs)} could be blocked."
        )

    edges = tuple(
        Edge(
            node_a=node_a,
            node_b=node_b,
            distance=distance_by_pair[(node_a, node_b)],
            available=(node_a, node_b) not in blocked_pairs,
        )
        for node_a, node_b in sorted_pairs
    )

    # Step 5: site attributes.
    sites = []
    for site_id in range(1, N_SITES + 1):
        people_affected = rng.randint(*PEOPLE_RANGE)
        priority = rng.randint(*PRIORITY_RANGE)
        demands = {}
        for resource in _RESOURCE_ORDER:
            rate = DEMAND_RATES_PER_100_PEOPLE[resource]
            noise = rng.uniform(*DEMAND_NOISE)
            demands[resource] = max(1, round(people_affected / 100 * rate * noise))
        benefit_fraction = rng.uniform(*BENEFIT_FRACTION_RANGE)
        expected_benefit = round(people_affected * benefit_fraction)
        x, y = positions[site_id]
        sites.append(
            Site(
                node_id=site_id,
                name=f"Site {site_id:02d}",
                x=x,
                y=y,
                people_affected=people_affected,
                priority=priority,
                water=demands["water"],
                medicine=demands["medicine"],
                food=demands["food"],
                hygiene_kits=demands["hygiene_kits"],
                blankets=demands["blankets"],
                expected_benefit=expected_benefit,
            )
        )

    return Instance(depot=depot, sites=tuple(sites), edges=edges)


def write_instance(instance: Instance, nodes_path: str | Path, edges_path: str | Path) -> None:
    """Write an Instance to the two CSV files, deterministically.

    Parameters
    ----------
    instance : Instance
        The instance to write.
    nodes_path : str | Path
        Destination for the nodes CSV (depot + sites, sorted by node_id).
    edges_path : str | Path
        Destination for the edges CSV (sorted by (node_a, node_b)).
    """
    nodes_path = Path(nodes_path)
    edges_path = Path(edges_path)
    nodes_path.parent.mkdir(parents=True, exist_ok=True)
    edges_path.parent.mkdir(parents=True, exist_ok=True)

    with open(nodes_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(NODE_COLUMNS)
        writer.writerow(
            (instance.depot.node_id, instance.depot.name, "depot", instance.depot.x, instance.depot.y,
             0, 0, 0, 0, 0, 0, 0, 0)
        )
        for site in sorted(instance.sites, key=lambda s: s.node_id):
            writer.writerow(
                (site.node_id, site.name, "site", site.x, site.y,
                 site.people_affected, site.priority,
                 site.water, site.medicine, site.food, site.hygiene_kits, site.blankets,
                 site.expected_benefit)
            )

    with open(edges_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(EDGE_COLUMNS)
        for edge in sorted(instance.edges, key=lambda e: (e.node_a, e.node_b)):
            writer.writerow((edge.node_a, edge.node_b, edge.distance, int(edge.available)))


def _euclidean(point_a: tuple[int, int], point_b: tuple[int, int]) -> float:
    """Euclidean distance between two integer grid points."""
    return math.dist(point_a, point_b)


def _all_reachable(
    node_ids: list[int],
    pairs: list[tuple[int, int]],
    blocked_pairs: set[tuple[int, int]],
) -> bool:
    """Check, by breadth-first search from the depot, that every node is still reachable.

    Parameters
    ----------
    node_ids : list[int]
        All node ids that must be reachable (depot included).
    pairs : list[tuple[int, int]]
        Every candidate road, as (node_a, node_b) with node_a < node_b.
    blocked_pairs : set[tuple[int, int]]
        The pairs to treat as unavailable for this check.

    Returns
    -------
    bool
        True if a breadth-first search from node 0 reaches every node in ``node_ids``.
    """
    adjacency: dict[int, list[int]] = {node_id: [] for node_id in node_ids}
    for node_a, node_b in pairs:
        if (node_a, node_b) in blocked_pairs:
            continue
        adjacency[node_a].append(node_b)
        adjacency[node_b].append(node_a)

    # Base case: the depot reaches itself with zero roads.
    visited = {0}
    queue = deque([0])
    while queue:
        current = queue.popleft()
        for neighbor in adjacency[current]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    return len(visited) == len(node_ids)


if __name__ == "__main__":
    _repo_root = Path(__file__).resolve().parent.parent
    _instance = generate_instance()
    write_instance(_instance, _repo_root / "data" / "problema1.csv", _repo_root / "data" / "problema1_edges.csv")
