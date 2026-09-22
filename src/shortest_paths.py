"""Question 1: Dijkstra's algorithm, path reconstruction, and distance matrices.

Distances are computed only over the *available* roads (Decision D6):
callers pass ``Instance.graph()``, which already excludes blocked edges.
"""

from __future__ import annotations

import heapq
import math

from src.estruturas import Graph


def dijkstra(graph: Graph, source: int) -> tuple[dict[int, float], dict[int, int | None]]:
    """Shortest distances and predecessor tree from a single source.

    Uses a binary heap (``heapq``) with lazy deletion: a heap entry that
    is no longer the best known distance for its node is simply skipped
    when popped, instead of being removed from the heap -- simpler to
    get right than a decrease-key operation, at the cost of the heap
    holding up to one stale entry per relaxation.

    Parameters
    ----------
    graph : Graph
        Adjacency list of available edges: node_id -> [(neighbor_id, distance), ...].
    source : int
        Node id to compute distances from.

    Returns
    -------
    tuple[dict[int, float], dict[int, int | None]]
        ``distance``: shortest distance from ``source`` to every node in
        ``graph`` (``math.inf`` if unreachable), with ``distance[source] == 0``.
        ``parent``: predecessor of each node on its shortest path
        (``None`` for ``source`` and for unreachable nodes).

    Raises
    ------
    ValueError
        If ``source`` is not a node of ``graph``, or any edge weight is not positive.
    """
    if source not in graph:
        raise ValueError(f"Unknown source node: {source}")
    for node, neighbors in graph.items():
        for _, weight in neighbors:
            if weight <= 0:
                raise ValueError(f"Non-positive edge weight found at node {node}: {weight}")

    distance: dict[int, float] = {node: math.inf for node in graph}
    parent: dict[int, int | None] = {node: None for node in graph}
    distance[source] = 0

    # heap entries are (distance, node_id); visited marks nodes whose
    # shortest distance is final, so a later, worse entry for the same
    # node is skipped (the lazy-deletion trick described above).
    heap: list[tuple[float, int]] = [(0, source)]
    visited: set[int] = set()

    # TIME: every node is popped at most once and every available edge is
    # relaxed at most twice (once from each endpoint); each heap push/pop
    # costs O(log V) -> O((V + E) log V).
    # MEMORY: distance, parent and visited hold one entry per node; the
    # heap holds at most one entry per relaxation, up to O(E) -> O(V + E).
    while heap:
        current_distance, node = heapq.heappop(heap)
        if node in visited:
            continue
        visited.add(node)

        for neighbor, weight in graph[node]:
            new_distance = current_distance + weight
            if new_distance < distance[neighbor]:
                distance[neighbor] = new_distance
                parent[neighbor] = node
                heapq.heappush(heap, (new_distance, neighbor))

    return distance, parent


def reconstruct_path(parent: dict[int, int | None], source: int, target: int) -> list[int] | None:
    """Rebuild the shortest path from ``source`` to ``target`` out of a parent map.

    Parameters
    ----------
    parent : dict[int, int | None]
        Predecessor map returned by :func:`dijkstra`.
    source : int
        Start node.
    target : int
        End node.

    Returns
    -------
    list[int] | None
        The path ``[source, ..., target]``, or ``None`` if ``target`` is
        not in ``parent`` or has no path back to ``source``.
    """
    if target not in parent:
        return None

    path = [target]
    current = target
    # TIME: the path has at most V nodes -> O(V).
    # MEMORY: the returned list holds at most V nodes -> O(V).
    while current != source:
        previous = parent[current]
        if previous is None:
            return None
        path.append(previous)
        current = previous
    path.reverse()
    return path


def distance_matrix(graph: Graph, sources: list[int]) -> dict[int, dict[int, float]]:
    """Run Dijkstra once per source and collect the resulting distances.

    Parameters
    ----------
    graph : Graph
        Adjacency list of available edges.
    sources : list[int]
        Node ids to compute distances from.

    Returns
    -------
    dict[int, dict[int, float]]
        ``matrix[source][target]`` is the shortest distance, or
        ``math.inf`` if ``target`` is unreachable from ``source``.
    """
    # TIME: one Dijkstra call per source -> O(|sources| * (V + E) log V).
    # MEMORY: one distance dict per source, each O(V) -> O(|sources| * V).
    matrix: dict[int, dict[int, float]] = {}
    for source in sources:
        distance, _ = dijkstra(graph, source)
        matrix[source] = distance
    return matrix
