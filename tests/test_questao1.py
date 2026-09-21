"""Tests for Question 1 (Emergency Logistics after Climate Events)."""

import csv
import math

import pytest

from src import data_generator, dynamic_programming, estruturas, greedy, objective
from src.data_generator import generate_instance, write_instance
from src.data_loader import load_instance
from src.estruturas import Site
from src.greedy import solve_greedy
from src.objective import build_order
from src.shortest_paths import dijkstra, distance_matrix, reconstruct_path


def test_question1_modules_import():
    # Proves the Question 1 module skeleton is importable before any algorithm exists.
    assert estruturas and greedy and dynamic_programming


# ----- Generator (Section 9.1) -----

def test_generate_instance_is_deterministic_for_the_same_seed():
    # Reproducibility requirement: the same seed must yield an identical Instance.
    assert generate_instance(seed=1) == generate_instance(seed=1)


def test_generate_instance_differs_across_seeds():
    # A different seed must not collapse onto the same dataset.
    assert generate_instance(seed=1) != generate_instance(seed=2)


def test_generate_instance_seed_1_meets_the_assignment_guarantees():
    # Checks the Part A hard requirements for SEED = 1: counts, connectivity, positive loads.
    instance = generate_instance(seed=data_generator.SEED)

    assert len(instance.sites) == data_generator.N_SITES

    available_edges = [edge for edge in instance.edges if edge.available]
    blocked_edges = [edge for edge in instance.edges if not edge.available]
    assert len(available_edges) >= 35
    assert len(blocked_edges) >= 6

    n_nodes = data_generator.N_SITES + 1
    assert len(instance.edges) < n_nodes * (n_nodes - 1) // 2

    distance, _ = dijkstra(instance.graph(), instance.depot.node_id)
    assert all(value < math.inf for value in distance.values())

    assert all(site.load > 0 for site in instance.sites)
    assert all(isinstance(site.load, int) for site in instance.sites)


def test_data_generator_seed_constant_is_1():
    # The seed must live in exactly one place (Section 2 of the spec).
    assert data_generator.SEED == 1


# ----- Site formulas (Decision D10) -----

def test_site_load_and_effective_benefit_formulas():
    # D10: load sums the five demands; effective_benefit multiplies benefit by priority.
    site = Site(
        node_id=1, name="Site 01", x=10, y=20,
        people_affected=500, priority=3,
        water=15, medicine=5, food=15, hygiene_kits=10, blankets=10,
        expected_benefit=400,
    )
    assert site.load == 55
    assert site.effective_benefit == 1200


# ----- Loader (Section 9.2) -----

NODE_HEADER = (
    "node_id", "name", "kind", "x", "y", "people_affected", "priority",
    "water", "medicine", "food", "hygiene_kits", "blankets", "expected_benefit",
)
EDGE_HEADER = ("node_a", "node_b", "distance", "available")
DEPOT_ROW = (0, "Distribution Center", "depot", 50, 50, 0, 0, 0, 0, 0, 0, 0, 0)
SITE_ROW = (1, "Site 01", "site", 10, 10, 500, 3, 15, 5, 15, 10, 10, 400)


def _write_csv(path, header, rows) -> None:
    """Write a minimal CSV for the loader error-path tests."""
    with open(path, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def test_write_then_load_instance_round_trips(tmp_path):
    # write_instance followed by load_instance must reproduce the same Instance.
    instance = generate_instance(seed=1)
    nodes_path = tmp_path / "nodes.csv"
    edges_path = tmp_path / "edges.csv"
    write_instance(instance, nodes_path, edges_path)
    assert load_instance(nodes_path, edges_path) == instance


def test_load_instance_missing_file_raises_value_error(tmp_path):
    # A missing CSV file must be reported as ValueError, not a raw FileNotFoundError.
    with pytest.raises(ValueError):
        load_instance(tmp_path / "missing_nodes.csv", tmp_path / "missing_edges.csv")


def test_load_instance_missing_column_raises_value_error(tmp_path):
    # A header lacking a required column must be rejected.
    nodes_path, edges_path = tmp_path / "nodes.csv", tmp_path / "edges.csv"
    _write_csv(nodes_path, NODE_HEADER[:-1], [DEPOT_ROW[:-1]])
    _write_csv(edges_path, EDGE_HEADER, [])
    with pytest.raises(ValueError):
        load_instance(nodes_path, edges_path)


def test_load_instance_non_integer_value_raises_value_error(tmp_path):
    # A non-integer cell where an integer is expected must be rejected.
    nodes_path, edges_path = tmp_path / "nodes.csv", tmp_path / "edges.csv"
    bad_row = (0, "Distribution Center", "depot", "not-a-number", 50, 0, 0, 0, 0, 0, 0, 0, 0)
    _write_csv(nodes_path, NODE_HEADER, [bad_row])
    _write_csv(edges_path, EDGE_HEADER, [])
    with pytest.raises(ValueError):
        load_instance(nodes_path, edges_path)


def test_load_instance_duplicated_node_id_raises_value_error(tmp_path):
    # Two rows sharing a node_id must be rejected.
    nodes_path, edges_path = tmp_path / "nodes.csv", tmp_path / "edges.csv"
    duplicate_row = (0, "Distribution Center 2", "depot", 60, 60, 0, 0, 0, 0, 0, 0, 0, 0)
    _write_csv(nodes_path, NODE_HEADER, [DEPOT_ROW, duplicate_row])
    _write_csv(edges_path, EDGE_HEADER, [])
    with pytest.raises(ValueError):
        load_instance(nodes_path, edges_path)


def test_load_instance_missing_depot_raises_value_error(tmp_path):
    # A nodes CSV with no depot row must be rejected.
    nodes_path, edges_path = tmp_path / "nodes.csv", tmp_path / "edges.csv"
    _write_csv(nodes_path, NODE_HEADER, [SITE_ROW])
    _write_csv(edges_path, EDGE_HEADER, [])
    with pytest.raises(ValueError):
        load_instance(nodes_path, edges_path)


def test_load_instance_unknown_kind_raises_value_error(tmp_path):
    # A kind other than 'depot' or 'site' must be rejected.
    nodes_path, edges_path = tmp_path / "nodes.csv", tmp_path / "edges.csv"
    bad_row = (1, "Site 01", "shelter", 10, 10, 500, 3, 15, 5, 15, 10, 10, 400)
    _write_csv(nodes_path, NODE_HEADER, [DEPOT_ROW, bad_row])
    _write_csv(edges_path, EDGE_HEADER, [])
    with pytest.raises(ValueError):
        load_instance(nodes_path, edges_path)


def test_load_instance_edge_unknown_node_raises_value_error(tmp_path):
    # An edge referencing a node id that does not exist must be rejected.
    nodes_path, edges_path = tmp_path / "nodes.csv", tmp_path / "edges.csv"
    _write_csv(nodes_path, NODE_HEADER, [DEPOT_ROW, SITE_ROW])
    _write_csv(edges_path, EDGE_HEADER, [(0, 99, 10, 1)])
    with pytest.raises(ValueError):
        load_instance(nodes_path, edges_path)


def test_load_instance_edge_node_a_not_smaller_raises_value_error(tmp_path):
    # node_a must be strictly smaller than node_b (canonical undirected pair).
    nodes_path, edges_path = tmp_path / "nodes.csv", tmp_path / "edges.csv"
    _write_csv(nodes_path, NODE_HEADER, [DEPOT_ROW, SITE_ROW])
    _write_csv(edges_path, EDGE_HEADER, [(1, 0, 10, 1)])
    with pytest.raises(ValueError):
        load_instance(nodes_path, edges_path)


def test_load_instance_duplicated_edge_raises_value_error(tmp_path):
    # The same (node_a, node_b) pair must not appear twice.
    nodes_path, edges_path = tmp_path / "nodes.csv", tmp_path / "edges.csv"
    _write_csv(nodes_path, NODE_HEADER, [DEPOT_ROW, SITE_ROW])
    _write_csv(edges_path, EDGE_HEADER, [(0, 1, 10, 1), (0, 1, 20, 1)])
    with pytest.raises(ValueError):
        load_instance(nodes_path, edges_path)


def test_load_instance_non_positive_distance_raises_value_error(tmp_path):
    # distance must be strictly positive.
    nodes_path, edges_path = tmp_path / "nodes.csv", tmp_path / "edges.csv"
    _write_csv(nodes_path, NODE_HEADER, [DEPOT_ROW, SITE_ROW])
    _write_csv(edges_path, EDGE_HEADER, [(0, 1, 0, 1)])
    with pytest.raises(ValueError):
        load_instance(nodes_path, edges_path)


def test_load_instance_available_not_0_or_1_raises_value_error(tmp_path):
    # available must be exactly '0' or '1'.
    nodes_path, edges_path = tmp_path / "nodes.csv", tmp_path / "edges.csv"
    _write_csv(nodes_path, NODE_HEADER, [DEPOT_ROW, SITE_ROW])
    _write_csv(edges_path, EDGE_HEADER, [(0, 1, 10, 2)])
    with pytest.raises(ValueError):
        load_instance(nodes_path, edges_path)


def test_load_instance_priority_out_of_range_raises_value_error(tmp_path):
    # priority must be in 1..5.
    nodes_path, edges_path = tmp_path / "nodes.csv", tmp_path / "edges.csv"
    bad_row = (1, "Site 01", "site", 10, 10, 500, 9, 15, 5, 15, 10, 10, 400)
    _write_csv(nodes_path, NODE_HEADER, [DEPOT_ROW, bad_row])
    _write_csv(edges_path, EDGE_HEADER, [])
    with pytest.raises(ValueError):
        load_instance(nodes_path, edges_path)


def test_load_instance_negative_demand_raises_value_error(tmp_path):
    # Every demand must be non-negative.
    nodes_path, edges_path = tmp_path / "nodes.csv", tmp_path / "edges.csv"
    bad_row = (1, "Site 01", "site", 10, 10, 500, 3, -1, 5, 15, 10, 10, 400)
    _write_csv(nodes_path, NODE_HEADER, [DEPOT_ROW, bad_row])
    _write_csv(edges_path, EDGE_HEADER, [])
    with pytest.raises(ValueError):
        load_instance(nodes_path, edges_path)


def test_load_instance_zero_load_raises_value_error(tmp_path):
    # A site whose five demands sum to zero (D2: 0/1 service) must be rejected.
    nodes_path, edges_path = tmp_path / "nodes.csv", tmp_path / "edges.csv"
    bad_row = (1, "Site 01", "site", 10, 10, 500, 3, 0, 0, 0, 0, 0, 400)
    _write_csv(nodes_path, NODE_HEADER, [DEPOT_ROW, bad_row])
    _write_csv(edges_path, EDGE_HEADER, [])
    with pytest.raises(ValueError):
        load_instance(nodes_path, edges_path)


# ----- Dijkstra (Decision D6) -----

def test_dijkstra_blocked_road_forces_a_detour():
    # No direct 0-1 road (blocked); the shortest path must detour through node 2.
    graph = {0: [(2, 4)], 1: [(2, 3)], 2: [(0, 4), (1, 3)]}
    distance, parent = dijkstra(graph, 0)
    assert distance[1] == 7
    assert parent[1] == 2


def test_dijkstra_unreachable_node_has_infinite_distance():
    # A node with no path from the source is reported as math.inf, not omitted.
    graph = {0: [(1, 1)], 1: [(0, 1)], 2: []}
    distance, _ = dijkstra(graph, 0)
    assert distance[2] == math.inf


def test_reconstruct_path_returns_the_expected_path():
    # The parent map must rebuild the exact detour path, not just its length.
    graph = {0: [(2, 4)], 1: [(2, 3)], 2: [(0, 4), (1, 3)]}
    _, parent = dijkstra(graph, 0)
    assert reconstruct_path(parent, 0, 1) == [0, 2, 1]


def test_dijkstra_unknown_source_raises_value_error():
    # A source outside the graph's nodes must be rejected explicitly.
    graph = {0: [(1, 1)], 1: [(0, 1)]}
    with pytest.raises(ValueError):
        dijkstra(graph, 99)


# ----- Canonical order pi (Decision D9) -----

def test_build_order_pre_order_with_tie_break_and_exclusions():
    # Pre-order DFS, children sorted by (distance, id) with a tie broken by id;
    # the depot and an unreachable node (5) must be excluded from the result.
    parent = {0: None, 1: 0, 2: 0, 3: 1, 4: 1, 5: None}
    distance = {0: 0, 1: 2, 2: 5, 3: 4, 4: 4, 5: math.inf}
    order = build_order(distance, parent, depot_id=0)
    assert order == [1, 3, 4, 2]
    assert 0 not in order
    assert 5 not in order


# ----- Lambda calibration (Decision D11) -----

def test_calibrate_lambda_uses_the_d11_median_rule():
    # lambda = round(median(effective_benefit) / median(distance from the depot)).
    assert objective.calibrate_lambda([10, 20, 30], [5, 10, 15]) == 2


def test_calibrate_lambda_empty_input_raises_value_error():
    # Calibration needs at least one candidate site.
    with pytest.raises(ValueError):
        objective.calibrate_lambda([], [])


def test_calibrate_lambda_non_positive_median_distance_raises_value_error():
    # A zero median distance (e.g. every site at the depot) cannot price distance.
    with pytest.raises(ValueError):
        objective.calibrate_lambda([10, 20], [0, 0])


def test_lambda_distance_price_matches_the_seed_1_calibration():
    # The hardcoded constant must match calibrate_lambda on the real dataset (D11).
    instance = generate_instance(seed=data_generator.SEED)
    distance, _ = dijkstra(instance.graph(), instance.depot.node_id)
    benefits = [site.effective_benefit for site in instance.sites]
    distances_from_depot = [distance[site.node_id] for site in instance.sites]
    assert objective.calibrate_lambda(benefits, distances_from_depot) == objective.LAMBDA_DISTANCE_PRICE


# ----- Route length, J(S) and marginal gain (Section 4) -----

def test_route_length_of_an_empty_set_is_zero():
    # L(emptyset) = 0: no distance is traveled if nothing is served.
    assert objective.route_length([], depot_id=0, distance={0: {0: 0}}) == 0


def test_route_length_sums_depot_to_first_then_consecutive_hops():
    # L({1,2}) = d(0,1) + d(1,2), sites visited in the given (pi) order.
    distance = {0: {0: 0, 1: 10, 2: 15}, 1: {0: 10, 1: 0, 2: 5}, 2: {0: 15, 1: 5, 2: 0}}
    assert objective.route_length([1, 2], depot_id=0, distance=distance) == 15


def test_objective_value_is_benefit_minus_lambda_times_route_length():
    # J(S) = sum(b_i) - lambda * L(S), per Section 4.
    distance = {0: {0: 0, 1: 10, 3: 15}, 1: {0: 10, 1: 0, 3: 5}, 3: {0: 15, 1: 5, 3: 0}}
    benefit = {1: 50, 3: 30}
    value = objective.objective_value([1, 3], depot_id=0, distance=distance, benefit=benefit, lambda_price=1)
    assert value == 65


def test_marginal_gain_when_candidate_would_be_last():
    # No successor: extra length is just d(predecessor, candidate).
    distance = {0: {0: 0, 1: 10}, 1: {0: 10, 1: 0}}
    gain = objective.marginal_gain(
        1, selected=[], pi_rank={1: 0}, depot_id=0, distance=distance, benefit={1: 100}, lambda_price=1
    )
    assert gain == 90  # 100 - 1 * d(0, 1)


def test_marginal_gain_with_a_successor_uses_the_detour_formula():
    # Section 4: inserting between p and s costs d(p,i) + d(i,s) - d(p,s).
    distance = {
        0: {0: 0, 1: 10, 2: 4, 3: 15},
        1: {0: 10, 1: 0, 2: 6, 3: 5},
        2: {0: 4, 1: 6, 2: 0, 3: 9},
        3: {0: 15, 1: 5, 2: 9, 3: 0},
    }
    gain = objective.marginal_gain(
        2, selected=[1, 3], pi_rank={1: 0, 2: 1, 3: 2}, depot_id=0,
        distance=distance, benefit={1: 50, 2: 20, 3: 30}, lambda_price=1,
    )
    assert gain == 10  # 20 - 1 * (d(1,2) + d(2,3) - d(1,3)) = 20 - (6 + 9 - 5)


# ----- Greedy solver (Decision D12) -----

def _small_greedy_instance() -> estruturas.Instance:
    """Depot with 2 cheap, high-benefit sites (1, 2) and 1 far, low-benefit site (3)."""
    depot = estruturas.Depot(node_id=0, name="Distribution Center", x=0, y=0)
    sites = (
        estruturas.Site(
            node_id=1, name="Site 01", x=0, y=0, people_affected=1, priority=1,
            water=5, medicine=0, food=0, hygiene_kits=0, blankets=0, expected_benefit=100,
        ),
        estruturas.Site(
            node_id=2, name="Site 02", x=0, y=0, people_affected=1, priority=1,
            water=5, medicine=0, food=0, hygiene_kits=0, blankets=0, expected_benefit=100,
        ),
        estruturas.Site(
            node_id=3, name="Site 03", x=0, y=0, people_affected=1, priority=1,
            water=1, medicine=0, food=0, hygiene_kits=0, blankets=0, expected_benefit=1,
        ),
    )
    edges = (
        estruturas.Edge(node_a=0, node_b=1, distance=10, available=True),
        estruturas.Edge(node_a=0, node_b=2, distance=100, available=True),
        estruturas.Edge(node_a=0, node_b=3, distance=100, available=True),
        estruturas.Edge(node_a=1, node_b=2, distance=5, available=True),
        estruturas.Edge(node_a=1, node_b=3, distance=5, available=True),
        estruturas.Edge(node_a=2, node_b=3, distance=5, available=True),
    )
    return estruturas.Instance(depot=depot, sites=sites, edges=edges)


def _greedy_inputs(instance: estruturas.Instance):
    """Shared plumbing: graph, pi order and full distance matrix for the small instance."""
    graph = instance.graph()
    distance_from_depot, parent = dijkstra(graph, instance.depot.node_id)
    pi_order = build_order(distance_from_depot, parent, instance.depot.node_id)
    distance = distance_matrix(graph, [instance.depot.node_id, *pi_order])
    return pi_order, distance


def test_solve_greedy_picks_the_two_densest_sites_and_stops():
    # Hand-traced: site 1 (score 18) beats site 2 (score 17) first; site 2 is then
    # cheap via site 1; site 3 never has positive marginal gain, so it is skipped.
    instance = _small_greedy_instance()
    pi_order, distance = _greedy_inputs(instance)

    solution = solve_greedy(instance, capacity=10, pi_order=pi_order, distance=distance, lambda_price=1)

    assert solution.selected_sites == (1, 2)
    assert solution.total_benefit == 200
    assert solution.total_load == 10
    assert solution.route_length == 15
    assert solution.objective_value == 185


def test_solve_greedy_zero_capacity_selects_nothing():
    # With no capacity, every candidate is unaffordable, so the plan is empty and J = 0.
    instance = _small_greedy_instance()
    pi_order, distance = _greedy_inputs(instance)
    solution = solve_greedy(instance, capacity=0, pi_order=pi_order, distance=distance, lambda_price=1)
    assert solution.selected_sites == ()
    assert solution.objective_value == 0


def test_solve_greedy_negative_capacity_raises_value_error():
    # Negative capacity is a malformed input (Section 5.1).
    instance = _small_greedy_instance()
    pi_order, distance = _greedy_inputs(instance)
    with pytest.raises(ValueError):
        solve_greedy(instance, capacity=-1, pi_order=pi_order, distance=distance)


def test_solve_greedy_non_positive_lambda_raises_value_error():
    # D11: lambda must be a positive integer.
    instance = _small_greedy_instance()
    pi_order, distance = _greedy_inputs(instance)
    with pytest.raises(ValueError):
        solve_greedy(instance, capacity=10, pi_order=pi_order, distance=distance, lambda_price=0)


def test_insert_in_pi_order_places_candidate_in_the_middle():
    # The internal helper must insert by pi rank, not just append at the end.
    selected = [1, 3]
    greedy._insert_in_pi_order(selected, 2, {1: 0, 2: 1, 3: 2})
    assert selected == [1, 2, 3]
