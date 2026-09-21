"""Question 1: canonical visiting order pi.

This step adds only ``build_order`` (Decision D9). Route length ``L(S)``,
the objective ``J(S)`` and the marginal insertion cost are added in Step 3.
"""

from __future__ import annotations


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
