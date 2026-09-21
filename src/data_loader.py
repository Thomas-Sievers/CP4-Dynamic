"""Question 1: reading and validating the CSV files into an Instance."""

from __future__ import annotations

import csv
from pathlib import Path

from src.estruturas import Depot, Edge, Instance, Site

NODE_COLUMNS = (
    "node_id", "name", "kind", "x", "y", "people_affected", "priority",
    "water", "medicine", "food", "hygiene_kits", "blankets", "expected_benefit",
)
EDGE_COLUMNS = ("node_a", "node_b", "distance", "available")


def load_instance(nodes_path: str | Path, edges_path: str | Path) -> Instance:
    """Load and validate a Question 1 Instance from the two CSV files.

    Parameters
    ----------
    nodes_path : str | Path
        Path to the nodes CSV (depot + sites).
    edges_path : str | Path
        Path to the edges CSV (roads, including blocked ones).

    Returns
    -------
    Instance
        The validated instance.

    Raises
    ------
    ValueError
        For any missing file/column, malformed value, or inconsistency
        listed in the module tests (duplicated ids, unknown references,
        out-of-range fields, and so on).
    """
    depot, sites, known_ids = _load_nodes(nodes_path)
    edges = _load_edges(edges_path, known_ids)
    return Instance(depot=depot, sites=tuple(sites), edges=tuple(edges))


def _read_rows(path: str | Path, expected_columns: tuple[str, ...]) -> list[dict[str, str]]:
    """Read a CSV file as a list of row dicts, after checking the header is complete."""
    path = Path(path)
    try:
        handle = open(path, "r", newline="", encoding="utf-8")
    except FileNotFoundError as error:
        raise ValueError(f"CSV file not found: {path}") from error

    with handle:
        reader = csv.DictReader(handle)
        missing = set(expected_columns) - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"{path} is missing column(s): {sorted(missing)}")
        return list(reader)


def _parse_int(value: str, field_name: str, row_number: int) -> int:
    """Parse a CSV cell as an integer, raising ValueError with row context on failure."""
    try:
        return int(value)
    except ValueError as error:
        raise ValueError(
            f"Row {row_number}: field '{field_name}' is not an integer: {value!r}"
        ) from error


def _load_nodes(nodes_path: str | Path) -> tuple[Depot, list[Site], set[int]]:
    """Load and validate the nodes CSV; return the depot, the sites, and the set of known ids."""
    rows = _read_rows(nodes_path, NODE_COLUMNS)

    depot: Depot | None = None
    sites: list[Site] = []
    seen_ids: set[int] = set()

    for row_number, row in enumerate(rows, start=2):  # row 1 is the header
        node_id = _parse_int(row["node_id"], "node_id", row_number)
        if node_id in seen_ids:
            raise ValueError(f"Row {row_number}: duplicated node_id {node_id}.")
        seen_ids.add(node_id)

        kind = row["kind"]
        x = _parse_int(row["x"], "x", row_number)
        y = _parse_int(row["y"], "y", row_number)

        if kind == "depot":
            if depot is not None:
                raise ValueError("More than one 'depot' row found in the nodes CSV.")
            if node_id != 0:
                raise ValueError(f"Row {row_number}: the depot row must have node_id 0, got {node_id}.")
            depot = Depot(node_id=node_id, name=row["name"], x=x, y=y)
        elif kind == "site":
            sites.append(
                Site(
                    node_id=node_id,
                    name=row["name"],
                    x=x,
                    y=y,
                    people_affected=_parse_int(row["people_affected"], "people_affected", row_number),
                    priority=_parse_int(row["priority"], "priority", row_number),
                    water=_parse_int(row["water"], "water", row_number),
                    medicine=_parse_int(row["medicine"], "medicine", row_number),
                    food=_parse_int(row["food"], "food", row_number),
                    hygiene_kits=_parse_int(row["hygiene_kits"], "hygiene_kits", row_number),
                    blankets=_parse_int(row["blankets"], "blankets", row_number),
                    expected_benefit=_parse_int(row["expected_benefit"], "expected_benefit", row_number),
                )
            )
        else:
            raise ValueError(f"Row {row_number}: unknown kind {kind!r} (expected 'depot' or 'site').")

    if depot is None:
        raise ValueError("The nodes CSV has no 'depot' row.")

    return depot, sites, seen_ids


def _load_edges(edges_path: str | Path, known_ids: set[int]) -> list[Edge]:
    """Load and validate the edges CSV against the known node ids."""
    rows = _read_rows(edges_path, EDGE_COLUMNS)

    edges: list[Edge] = []
    seen_pairs: set[tuple[int, int]] = set()

    for row_number, row in enumerate(rows, start=2):
        node_a = _parse_int(row["node_a"], "node_a", row_number)
        node_b = _parse_int(row["node_b"], "node_b", row_number)
        distance = _parse_int(row["distance"], "distance", row_number)

        available_raw = row["available"]
        if available_raw not in ("0", "1"):
            raise ValueError(f"Row {row_number}: 'available' must be 0 or 1, got {available_raw!r}.")

        if node_a not in known_ids or node_b not in known_ids:
            raise ValueError(f"Row {row_number}: edge references an unknown node ({node_a}, {node_b}).")

        pair = (node_a, node_b)
        if pair in seen_pairs:
            raise ValueError(f"Row {row_number}: duplicated edge {pair}.")
        seen_pairs.add(pair)

        edges.append(Edge(node_a=node_a, node_b=node_b, distance=distance, available=available_raw == "1"))

    return edges
