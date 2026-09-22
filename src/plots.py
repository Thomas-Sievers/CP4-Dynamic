"""Question 1: figures for Part E and Part F (Section 5.2 figure conventions).

Four plotting functions, each returning a ``matplotlib.figure.Figure``:

1. ``plot_instance_graph`` -- depot, sites, roads, weights, blocked roads (Figure 1, Part E).
2. ``plot_solution`` -- served/not-served sites and the service route (Figure 2, Part E).
3. ``plot_dp_table`` -- the DP value table, reconstruction path, decision cells (Figure 3, Part E).
4. ``plot_time_growth`` -- measured time vs. N against an O(2^N) reference (Figure 4, Part F).

Running ``python -m src.plots`` regenerates all four PNGs used in the
README/notebook into ``figures/questao1/``, from the real seed-1 dataset.
Library code here never calls ``plt.show()``; the caller decides whether
to display or save (Section 5.2, "code returns data").
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle

from src.dynamic_programming import UNREACHABLE, solve_dp
from src.estruturas import Instance, Solution
from src.objective import LAMBDA_DISTANCE_PRICE, build_order
from src.shortest_paths import dijkstra, distance_matrix

FIGSIZE = (9, 5.5)
ROUTE_COLOR = "tab:blue"
UNSELECTED_COLOR = "0.6"
BLOCKED_COLOR = "tab:red"
DEPOT_COLOR = "black"
DECISION_COLOR = "tab:orange"

_MAX_ANNOTATED_CELLS = 400  # writing a value in every cell stays readable up to this size


def _site_positions(instance: Instance) -> dict[int, tuple[int, int]]:
    """node_id -> (x, y) for the depot and every site, straight from the data."""
    positions = {instance.depot.node_id: (instance.depot.x, instance.depot.y)}
    for site in instance.sites:
        positions[site.node_id] = (site.x, site.y)
    return positions


def plot_instance_graph(instance: Instance, ax: plt.Axes | None = None) -> plt.Figure:
    """Figure 1: the service network -- depot, sites, roads, weights, blocked roads.

    Parameters
    ----------
    instance : Instance
        The dataset to draw.
    ax : matplotlib.axes.Axes, optional
        Axes to draw into; a new figure is created if omitted.

    Returns
    -------
    matplotlib.figure.Figure
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=FIGSIZE)
    else:
        fig = ax.figure

    positions = _site_positions(instance)

    for edge in instance.edges:
        x1, y1 = positions[edge.node_a]
        x2, y2 = positions[edge.node_b]
        if edge.available:
            ax.plot([x1, x2], [y1, y2], color=UNSELECTED_COLOR, linewidth=1.2, zorder=1)
        else:
            ax.plot([x1, x2], [y1, y2], color=BLOCKED_COLOR, linewidth=1.2, linestyle="--", zorder=1)
        mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(
            mid_x, mid_y, str(edge.distance), fontsize=6.5, ha="center", va="center", zorder=3,
            bbox=dict(facecolor="white", edgecolor="none", pad=0.5, alpha=0.85),
        )

    for site in instance.sites:
        x, y = positions[site.node_id]
        ax.add_patch(Circle((x, y), radius=2.0, facecolor="white", edgecolor="black", zorder=2))
        ax.text(x, y, str(site.node_id), fontsize=7.5, ha="center", va="center", zorder=4)

    depot_x, depot_y = positions[instance.depot.node_id]
    ax.add_patch(Circle((depot_x, depot_y), radius=2.6, facecolor=DEPOT_COLOR, zorder=2))
    ax.text(depot_x, depot_y, "D", fontsize=9, color="white", ha="center", va="center", weight="bold", zorder=4)

    ax.set_title("Figure 1 - Service network: depot, sites, roads and weights")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_aspect("equal")
    ax.margins(0.1)

    legend_elements = [
        Line2D([0], [0], color=UNSELECTED_COLOR, lw=1.2, label="Available road"),
        Line2D([0], [0], color=BLOCKED_COLOR, lw=1.2, linestyle="--", label="Blocked road"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor=DEPOT_COLOR, markersize=9, label="Distribution center"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="white", markeredgecolor="black", markersize=9, label="Site"),
    ]
    ax.legend(handles=legend_elements, loc="best", fontsize=8, framealpha=0.9)
    return fig


def plot_solution(instance: Instance, solution: Solution, ax: plt.Axes | None = None) -> plt.Figure:
    """Figure 2: served vs. not-served sites and the service route, in pi order.

    Parameters
    ----------
    instance : Instance
        The dataset the solution was computed on.
    solution : Solution
        A Greedy or DP result (same shape either way, D15).
    ax : matplotlib.axes.Axes, optional
        Axes to draw into; a new figure is created if omitted.

    Returns
    -------
    matplotlib.figure.Figure
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=FIGSIZE)
    else:
        fig = ax.figure

    positions = _site_positions(instance)

    for edge in instance.edges:
        if not edge.available:
            continue
        x1, y1 = positions[edge.node_a]
        x2, y2 = positions[edge.node_b]
        ax.plot([x1, x2], [y1, y2], color="0.88", linewidth=1.0, zorder=1)

    route_nodes = [instance.depot.node_id, *solution.selected_sites]
    for node_a, node_b in zip(route_nodes, route_nodes[1:]):
        x1, y1 = positions[node_a]
        x2, y2 = positions[node_b]
        arrow = FancyArrowPatch(
            (x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=14,
            color=ROUTE_COLOR, linewidth=2.0, shrinkA=11, shrinkB=11, zorder=3,
        )
        ax.add_patch(arrow)

    served = set(solution.selected_sites)
    for site in instance.sites:
        x, y = positions[site.node_id]
        is_served = site.node_id in served
        face = ROUTE_COLOR if is_served else "white"
        edge_color = ROUTE_COLOR if is_served else UNSELECTED_COLOR
        text_color = "white" if is_served else "black"
        ax.add_patch(Circle((x, y), radius=2.0, facecolor=face, edgecolor=edge_color, linewidth=1.5, zorder=2))
        ax.text(x, y, str(site.node_id), fontsize=7.5, ha="center", va="center", color=text_color, zorder=4)

    depot_x, depot_y = positions[instance.depot.node_id]
    ax.add_patch(Circle((depot_x, depot_y), radius=2.6, facecolor=DEPOT_COLOR, zorder=2))
    ax.text(depot_x, depot_y, "D", fontsize=9, color="white", ha="center", va="center", weight="bold", zorder=4)

    ax.set_title(f"Figure 2 - Service plan: {len(served)} sites served, J(S) = {solution.objective_value}")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_aspect("equal")
    ax.margins(0.1)

    legend_elements = [
        Line2D([0], [0], color=ROUTE_COLOR, lw=2, label="Service route"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor=ROUTE_COLOR, markersize=9, label="Served site"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="white", markeredgecolor=UNSELECTED_COLOR, markersize=9, label="Not served"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor=DEPOT_COLOR, markersize=9, label="Distribution center"),
    ]
    ax.legend(handles=legend_elements, loc="best", fontsize=8, framealpha=0.9)
    return fig


def plot_dp_table(
    instance: Instance,
    dp: list[list[float]],
    pi_order: list[int],
    solution: Solution,
    ax: plt.Axes | None = None,
) -> plt.Figure:
    """Figure 3: the DP value table, with the reconstruction path over it.

    Parameters
    ----------
    instance : Instance
        The dataset (needed to look up each selected site's load).
    dp : list[list[float]]
        The value table returned by ``dynamic_programming.solve_dp``.
    pi_order : list[int]
        The same candidate order used to compute dp.
    solution : Solution
        The DP result for this table (drives the reconstruction path and summary).
    ax : matplotlib.axes.Axes, optional
        Axes to draw into; a new figure is created if omitted.

    Returns
    -------
    matplotlib.figure.Figure
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=FIGSIZE)
    else:
        fig = ax.figure

    n_rows = len(dp)
    n_cols = len(dp[0]) if dp else 0
    displayed = [[value if value != UNREACHABLE else float("nan") for value in row] for row in dp]

    cmap = plt.get_cmap("viridis").with_extremes(bad="0.92")
    image = ax.imshow(displayed, aspect="auto", origin="lower", cmap=cmap)
    colorbar = fig.colorbar(image, ax=ax)
    colorbar.set_label("J(S) for a route ending here")

    # Writing every value stays readable only up to a few hundred cells;
    # past that the colorbar and the reconstruction path carry the figure.
    if n_rows * n_cols <= _MAX_ANNOTATED_CELLS:
        for i in range(n_rows):
            for c in range(n_cols):
                value = dp[i][c]
                if value != UNREACHABLE:
                    ax.text(c, i, f"{int(value)}", ha="center", va="center", fontsize=6)

    path_cells: list[tuple[int, int]] = []
    running_load = 0
    for site_id in solution.selected_sites:
        running_load += instance.site_by_id(site_id).load
        path_cells.append((pi_order.index(site_id), running_load))

    if path_cells:
        rows = [cell[0] for cell in path_cells]
        cols = [cell[1] for cell in path_cells]
        ax.plot(
            cols, rows, color="white", linewidth=2.2, marker="o", markersize=7,
            markerfacecolor=DECISION_COLOR, markeredgecolor="black", zorder=5, label="Reconstruction path",
        )
        for row, col in path_cells:
            ax.add_patch(
                Rectangle((col - 0.5, row - 0.5), 1, 1, fill=False, edgecolor=DECISION_COLOR, linewidth=2, zorder=6)
            )
        ax.legend(loc="upper left", fontsize=8, framealpha=0.9)

    ax.set_title("Figure 3 - DP evolution: value table and reconstruction")
    ax.set_xlabel("load c")
    ax.set_ylabel("site (pi order)")
    if n_rows <= 30:
        ax.set_yticks(range(n_rows))
        ax.set_yticklabels([str(site_id) for site_id in pi_order], fontsize=7)

    summary = (
        f"Best J(S) = {solution.objective_value}\n"
        f"Selected sites (pi order): {solution.selected_sites}\n"
        f"Total load = {solution.total_load} | Route length = {solution.route_length}"
    )
    ax.text(
        0.01, -0.16, summary, transform=ax.transAxes, ha="left", va="top", fontsize=8,
        bbox=dict(facecolor="white", edgecolor="0.5", boxstyle="round"),
    )
    fig.subplots_adjust(bottom=0.28)
    return fig


def plot_time_growth(
    n_values: list[int],
    dp_times: list[float],
    greedy_times: list[float] | None = None,
    ax: plt.Axes | None = None,
) -> plt.Figure:
    """Part F supplementary figure: measured time vs. N, log scale, vs. an O(2^N) reference.

    Parameters
    ----------
    n_values : list[int]
        Candidate-set sizes that were swept (x axis).
    dp_times : list[float]
        Average ``solve_dp`` seconds at each entry of ``n_values``.
    greedy_times : list[float], optional
        Average ``solve_greedy`` seconds at each entry of ``n_values``.
    ax : matplotlib.axes.Axes, optional
        Axes to draw into; a new figure is created if omitted.

    Returns
    -------
    matplotlib.figure.Figure
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=FIGSIZE)
    else:
        fig = ax.figure

    ax.plot(n_values, dp_times, marker="o", color="tab:blue", label="DP (measured)")
    if greedy_times is not None:
        ax.plot(n_values, greedy_times, marker="s", color="tab:green", label="Greedy (measured)")

    # A conceptual O(2^N) reference, scaled to match the DP curve at the
    # smallest N so only the *growth rate* is compared (Lesson 12, Cell
    # 07) -- this is a plotted formula, not a real brute-force run (2^20
    # subsets would dwarf the polynomial algorithms it exists to contrast).
    first_dp_time = dp_times[0] if dp_times and dp_times[0] > 0 else 1e-6
    scale = first_dp_time / (2**n_values[0])
    reference = [scale * (2**n) for n in n_values]
    ax.plot(n_values, reference, linestyle="--", color="0.4", label="O(2^N) reference (scaled)")

    ax.set_yscale("log")
    ax.set_title("Figure 4 - Time growth: DP/Greedy (measured) vs. O(2^N) reference")
    ax.set_xlabel("N (candidate sites)")
    ax.set_ylabel("average time per call (s, log scale)")
    ax.legend(loc="best", fontsize=8, framealpha=0.9)
    return fig


def demo_subset_for_figure_3(pi_order: list[int], n_sites: int = 4) -> list[int]:
    """First n_sites of pi_order: few enough real sites for a fully-annotated Figure 3."""
    return pi_order[:n_sites]


def demo_capacity_for_figure_3(instance: Instance, demo_sites: list[int], fraction: float = 0.5) -> int:
    """A capacity for the demo sites that keeps the table within _MAX_ANNOTATED_CELLS.

    Using the real per-site loads (not invented numbers) at a smaller
    fraction than the notebook's default capacity, capped so
    ``len(demo_sites) * (capacity + 1) <= _MAX_ANNOTATED_CELLS`` and every
    cell of Figure 3 can show its value, as the spec asks.
    """
    total_load = sum(instance.site_by_id(site_id).load for site_id in demo_sites)
    capacity = int(fraction * total_load)
    max_capacity = _MAX_ANNOTATED_CELLS // len(demo_sites) - 1
    return min(capacity, max_capacity)


def generate_all_figures(output_dir: str | Path) -> None:
    """Load the seed-1 dataset, solve it, and save the three required figures.

    Figures 1 and 2 use the real dataset at the default capacity
    (``CAPACITY_FRACTION`` of the total load). Figure 3 reruns the DP on a
    small subset of the same real sites (the first few in pi order) purely
    so every cell of the table can be annotated and stay readable -- the
    full table (20 x ~580 cells) is shown by the colorbar and path alone
    in the notebook, but is too dense to annotate cell by cell here.

    Parameters
    ----------
    output_dir : str | Path
        Directory to save the three PNGs into (``figures/questao1``).
    """
    from src.data_generator import CAPACITY_FRACTION, SEED, generate_instance

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    instance = generate_instance(seed=SEED)
    graph = instance.graph()
    depot_id = instance.depot.node_id
    distance_from_depot, parent = dijkstra(graph, depot_id)
    pi_order = build_order(distance_from_depot, parent, depot_id)
    distance = distance_matrix(graph, [depot_id, *pi_order])
    capacity = int(CAPACITY_FRACTION * sum(site.load for site in instance.sites))

    fig1 = plot_instance_graph(instance)
    fig1.savefig(output_dir / "figure1_graph.png", dpi=150, bbox_inches="tight")
    plt.close(fig1)

    dp_solution, _ = solve_dp(
        instance, capacity=capacity, pi_order=pi_order, distance=distance, lambda_price=LAMBDA_DISTANCE_PRICE
    )
    fig2 = plot_solution(instance, dp_solution)
    fig2.savefig(output_dir / "figure2_solution.png", dpi=150, bbox_inches="tight")
    plt.close(fig2)

    demo_sites = demo_subset_for_figure_3(pi_order)
    demo_capacity = demo_capacity_for_figure_3(instance, demo_sites)
    demo_solution, demo_dp = solve_dp(
        instance, capacity=demo_capacity, pi_order=demo_sites, distance=distance, lambda_price=LAMBDA_DISTANCE_PRICE
    )
    fig3 = plot_dp_table(instance, demo_dp, demo_sites, demo_solution)
    fig3.savefig(output_dir / "figure3_dp_evolution.png", dpi=150, bbox_inches="tight")
    plt.close(fig3)


def generate_complexity_figure(output_dir: str | Path) -> None:
    """Measure Greedy/DP time growth on the real dataset and save Figure 4 (Part F).

    Parameters
    ----------
    output_dir : str | Path
        Directory to save the PNG into (``figures/questao1``).
    """
    from src.data_generator import SEED, generate_instance
    from src.measurements import sweep_dp_time_by_n, sweep_greedy_time_by_n

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    instance = generate_instance(seed=SEED)
    graph = instance.graph()
    depot_id = instance.depot.node_id
    distance_from_depot, parent = dijkstra(graph, depot_id)
    pi_order = build_order(distance_from_depot, parent, depot_id)
    distance = distance_matrix(graph, [depot_id, *pi_order])

    dp_points = sweep_dp_time_by_n(instance, pi_order, distance)
    greedy_points = sweep_greedy_time_by_n(instance, pi_order, distance)
    n_values = [n for n, _ in dp_points]
    dp_times = [t for _, t in dp_points]
    greedy_times = [t for _, t in greedy_points]

    fig4 = plot_time_growth(n_values, dp_times, greedy_times)
    fig4.savefig(output_dir / "figure4_complexity_growth.png", dpi=150, bbox_inches="tight")
    plt.close(fig4)


if __name__ == "__main__":
    _repo_root = Path(__file__).resolve().parent.parent
    _output_dir = _repo_root / "figures" / "questao1"
    generate_all_figures(_output_dir)
    generate_complexity_figure(_output_dir)
