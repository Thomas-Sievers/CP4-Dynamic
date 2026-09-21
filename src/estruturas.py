"""Shared data structures for Question 1 and Question 2.

Question 1 (emergency logistics) defines its types inside a delimited
``# ===== Question 1 =====`` block, added in Step 2: ``Depot``, ``Site``,
``Edge``, ``Instance``, the ``Graph`` type alias, and later ``Solution``.
Question 2 (energy consumption management) adds its own delimited block.
"""

from __future__ import annotations

from dataclasses import dataclass

# ===== Question 1 =====

# Adjacency list of available roads: node_id -> [(neighbor_id, distance), ...].
# A dict gives O(1) access from a node to its neighbors (Lesson 14 WeightedDAG style).
Graph = dict[int, list[tuple[int, int]]]


@dataclass(frozen=True, slots=True)
class Depot:
    """The single distribution center (node id 0)."""

    node_id: int
    name: str
    x: int
    y: int

    def __post_init__(self) -> None:
        # Base case of the whole model: there is exactly one depot, and it is node 0.
        if self.node_id != 0:
            raise ValueError(f"Depot node_id must be 0, got {self.node_id}.")


@dataclass(frozen=True, slots=True)
class Site:
    """A candidate service point, with its demands and expected benefit.

    ``load`` and ``effective_benefit`` (D10) are derived properties, not
    stored fields, so editing any single demand, the priority or the
    expected benefit automatically changes them -- needed for the live
    input changes during the defense.
    """

    node_id: int
    name: str
    x: int
    y: int
    people_affected: int
    priority: int
    water: int
    medicine: int
    food: int
    hygiene_kits: int
    blankets: int
    expected_benefit: int

    def __post_init__(self) -> None:
        if self.node_id <= 0:
            raise ValueError(f"Site node_id must be positive, got {self.node_id}.")
        if not (1 <= self.priority <= 5):
            raise ValueError(f"Site {self.node_id}: priority must be in 1..5, got {self.priority}.")
        for field_name, value in (
            ("people_affected", self.people_affected),
            ("water", self.water),
            ("medicine", self.medicine),
            ("food", self.food),
            ("hygiene_kits", self.hygiene_kits),
            ("blankets", self.blankets),
            ("expected_benefit", self.expected_benefit),
        ):
            if value < 0:
                raise ValueError(f"Site {self.node_id}: {field_name} must be non-negative, got {value}.")
        if self.load <= 0:
            raise ValueError(f"Site {self.node_id}: load (sum of demands) must be positive, got {self.load}.")

    @property
    def load(self) -> int:
        """Integer load in D1's single "load units": the sum of the five demands."""
        return self.water + self.medicine + self.food + self.hygiene_kits + self.blankets

    @property
    def effective_benefit(self) -> int:
        """D10: expected benefit scaled by priority, the value the algorithms optimize."""
        return self.expected_benefit * self.priority


@dataclass(frozen=True, slots=True)
class Edge:
    """An undirected road between two nodes, possibly blocked."""

    node_a: int
    node_b: int
    distance: int
    available: bool

    def __post_init__(self) -> None:
        if self.node_a >= self.node_b:
            raise ValueError(
                f"Edge node_a must be smaller than node_b, got ({self.node_a}, {self.node_b})."
            )
        if self.distance <= 0:
            raise ValueError(
                f"Edge ({self.node_a}, {self.node_b}): distance must be positive, got {self.distance}."
            )


@dataclass(frozen=True, slots=True)
class Instance:
    """The full Question 1 dataset: one depot, its candidate sites and the roads between them."""

    depot: Depot
    sites: tuple[Site, ...]
    edges: tuple[Edge, ...]

    def graph(self) -> Graph:
        """Build the adjacency list of the available edges only.

        Returns
        -------
        Graph
            node_id -> list of (neighbor_id, distance), available edges only.
        """
        adjacency: Graph = {self.depot.node_id: []}
        for site in self.sites:
            adjacency[site.node_id] = []
        for edge in self.edges:
            if not edge.available:
                continue
            adjacency[edge.node_a].append((edge.node_b, edge.distance))
            adjacency[edge.node_b].append((edge.node_a, edge.distance))
        return adjacency

    def site_by_id(self, node_id: int) -> Site:
        """Look up a site by its node_id.

        Parameters
        ----------
        node_id : int
            The id to search for.

        Returns
        -------
        Site
            The matching site.

        Raises
        ------
        ValueError
            If no site has this node_id.
        """
        for site in self.sites:
            if site.node_id == node_id:
                return site
        raise ValueError(f"Unknown site node_id: {node_id}")


# ===== end Question 1 =====
