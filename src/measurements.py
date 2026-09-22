"""Question 1: time and memory measurement helpers (Lesson 11, Cells 13-14).

Library code here never prints; it returns data for the notebook and
``docs/analise_complexidade.md`` to summarize, table and plot. Results are
empirical trends, not proof of the asymptotic complexity documented next
to each algorithm -- see the "Big O vs. measured time" note in the
complexity doc (Section 5.2, Lesson 11 section 12).
"""

from __future__ import annotations

import time
import tracemalloc
from typing import Callable

from src.dynamic_programming import solve_dp
from src.estruturas import Instance
from src.greedy import solve_greedy


def measure_time(function: Callable[..., object], data: tuple, repetitions: int = 5) -> float:
    """Average wall-clock time of ``function(*data)`` over repeated calls.

    Parameters
    ----------
    function : Callable
        The function to measure.
    data : tuple
        Positional arguments passed to ``function`` on every call.
    repetitions : int
        Number of repeated calls to average over, to smooth out timer and
        OS scheduling noise (Lesson 11, Cell 13).

    Returns
    -------
    float
        Average seconds per call, from ``time.perf_counter``.

    Raises
    ------
    ValueError
        If repetitions is not positive.
    """
    if repetitions <= 0:
        raise ValueError(f"repetitions must be positive, got {repetitions}.")

    total_seconds = 0.0
    for _ in range(repetitions):
        start = time.perf_counter()
        function(*data)
        end = time.perf_counter()
        total_seconds += end - start
    return total_seconds / repetitions


def peak_memory_bytes(function: Callable[..., object], data: tuple) -> int:
    """Peak memory allocated by one call to ``function(*data)``, via tracemalloc.

    Limits of this measurement (document alongside any number it
    produces): ``tracemalloc`` only tracks memory allocated through
    Python's own allocator, so it misses memory used by C-extension
    buffers, and it adds its own bookkeeping overhead -- it is a trend
    indicator, not an exact byte count.

    Parameters
    ----------
    function : Callable
        The function to measure.
    data : tuple
        Positional arguments passed to ``function``.

    Returns
    -------
    int
        Peak traced memory, in bytes, during the call.
    """
    tracemalloc.start()
    try:
        function(*data)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return peak


def sweep_dp_time_by_n(
    instance: Instance,
    pi_order: list[int],
    distance: dict[int, dict[int, float]],
    capacity_fraction: float = 0.35,
    repetitions: int = 5,
) -> list[tuple[int, float]]:
    """Average solve_dp time for increasing candidate-set sizes N.

    Each N uses the first N sites of ``pi_order`` (a real, already-solved
    prefix of the actual dataset, not synthetic data) and a capacity
    scaled to that subset's total load, so every point is a genuine,
    solvable instance.

    Parameters
    ----------
    instance : Instance
        The dataset the candidates come from.
    pi_order : list[int]
        The full candidate order; sizes 2..len(pi_order) are swept.
    distance : dict[int, dict[int, float]]
        Pairwise shortest distances covering depot + pi_order.
    capacity_fraction : float
        Fraction of the subset's total load used as capacity (D14's rule).
    repetitions : int
        Passed through to ``measure_time``.

    Returns
    -------
    list[tuple[int, float]]
        (N, average_seconds) pairs, N ascending.
    """
    results = []
    for n in range(2, len(pi_order) + 1):
        subset = pi_order[:n]
        capacity = max(1, int(capacity_fraction * sum(instance.site_by_id(site).load for site in subset)))
        avg_seconds = measure_time(solve_dp, (instance, capacity, subset, distance), repetitions)
        results.append((n, avg_seconds))
    return results


def sweep_greedy_time_by_n(
    instance: Instance,
    pi_order: list[int],
    distance: dict[int, dict[int, float]],
    capacity_fraction: float = 0.35,
    repetitions: int = 5,
) -> list[tuple[int, float]]:
    """Average solve_greedy time for increasing candidate-set sizes N (see sweep_dp_time_by_n)."""
    results = []
    for n in range(2, len(pi_order) + 1):
        subset = pi_order[:n]
        capacity = max(1, int(capacity_fraction * sum(instance.site_by_id(site).load for site in subset)))
        avg_seconds = measure_time(solve_greedy, (instance, capacity, subset, distance), repetitions)
        results.append((n, avg_seconds))
    return results


def sweep_dp_time_by_capacity(
    instance: Instance,
    pi_order: list[int],
    distance: dict[int, dict[int, float]],
    capacities: list[int],
    repetitions: int = 5,
) -> list[tuple[int, float]]:
    """Average solve_dp time for a list of capacities, at the full candidate set N.

    Parameters
    ----------
    instance : Instance
        The dataset (all of pi_order is used as the candidate set).
    pi_order : list[int]
        The full candidate order.
    distance : dict[int, dict[int, float]]
        Pairwise shortest distances covering depot + pi_order.
    capacities : list[int]
        Capacity values to measure, in the order given.
    repetitions : int
        Passed through to ``measure_time``.

    Returns
    -------
    list[tuple[int, float]]
        (capacity, average_seconds) pairs, in the order of ``capacities``.
    """
    results = []
    for capacity in capacities:
        avg_seconds = measure_time(solve_dp, (instance, capacity, pi_order, distance), repetitions)
        results.append((capacity, avg_seconds))
    return results
