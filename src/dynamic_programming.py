"""Question 1: Dynamic Programming solver.

Implements ``solve_dp``, a bottom-up DP over states ``(last site, load)``
that finds the combination of service points maximizing the shared
objective ``J(S)`` within vehicle capacity, plus reconstruction of the
chosen set from the stored predecessor table.
"""
