# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
#
# Data Envelopment Analysis (DEA) routines using open-source LP solvers.
#
# Refactored for compatibility with the Digital Public Goods Alliance (DPGA)
# Standard. The original implementation depended on Gurobi (proprietary,
# commercial-licensed), which precludes the project from meeting DPG
# Indicator 4 (Platform Independence). This module replaces that dependency
# with PuLP and its bundled CBC solver, both OSI-approved open source.
#
# Original algorithmic structure adapted from:
#   https://github.com/wurmen/DEA

"""Data Envelopment Analysis (DEA) using open-source LP solvers.

Public API
----------
CRS                Solve the constant-returns-to-scale DEA model.
VRS                Solve the variable-returns-to-scale DEA model.

Each solver routine returns a ``pandas.DataFrame`` with columns
``['DMU', 'efficiency']``. For input-oriented models the efficiency lies
in ``(0, 1]``; for output-oriented models it is reported as
``1 / objective`` so that ``1.0`` again denotes a fully efficient unit.

Intended use and limitations
----------------------------
This module computes DEA efficiency scores from numeric input/output
tables. It is intended as a component of a larger risk-modelling
pipeline and **should not** be used as the sole basis for decisions
that affect individuals or households. DMU identifiers are expected to
be non-personal (e.g. administrative unit codes); do not feed personal
identifiers into this routine.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Sequence, Tuple

import pandas as pd
from pulp import (
    LpMaximize,
    LpMinimize,
    LpProblem,
    LpStatus,
    LpStatusOptimal,
    LpVariable,
    PULP_CBC_CMD,
    lpSum,
    value,
)

logger = logging.getLogger(__name__)

# Type aliases for clarity
DMUData = Dict[str, List[float]]


# ---------------------------------------------------------------------------
# Solver helpers
# ---------------------------------------------------------------------------

# A single CBC solver instance is reused across LPs. ``msg=False`` silences
# the underlying CBC chatter; use the module logger for any reporting.
_CBC = PULP_CBC_CMD(msg=False)

# Big-M bound used in place of "free" variables (u0, v0) in the VRS
# multiplier forms. These variables are theoretically unrestricted in sign,
# but leaving them unbounded creates a degenerate unbounded ray in the LP
# under certain inputs (e.g. constant output vectors), which causes CBC to
# return spurious "optimal" solutions where constraint violations within
# solver tolerance scale up to noticeable errors in the reported
# efficiency. The bound matches the original Gurobi implementation and is
# large enough not to bind on any realistic DEA problem provided inputs
# and outputs are pre-scaled to roughly unit magnitude.
_FREE_BOUND = 1000


def _solve_or_raise(prob: LpProblem, dmu: str) -> float:
    """Solve ``prob`` and return its objective value, or raise."""
    status = prob.solve(_CBC)
    if status != LpStatusOptimal:
        raise RuntimeError(
            f"LP for DMU {dmu!r} terminated with status "
            f"{LpStatus[status]!r}; cannot report efficiency."
        )
    obj = value(prob.objective)
    if obj is None:
        return 0.0
    return float(obj)


def _validate_shapes(
    dmus: Sequence[str], x: DMUData, y: DMUData
) -> Tuple[int, int]:
    """Check that all DMUs share a consistent input/output dimensionality."""
    if not dmus:
        raise ValueError("No DMUs supplied.")
    n_in = len(x[dmus[0]])
    n_out = len(y[dmus[0]])
    for k in dmus:
        if len(x[k]) != n_in:
            raise ValueError(
                f"DMU {k!r} has {len(x[k])} inputs, expected {n_in}."
            )
        if len(y[k]) != n_out:
            raise ValueError(
                f"DMU {k!r} has {len(y[k])} outputs, expected {n_out}."
            )
    return n_in, n_out


def _result_frame(rows: List[Tuple[str, float]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["DMU", "efficiency"])


# ---------------------------------------------------------------------------
# CRS (Charnes-Cooper-Rhodes) models
# ---------------------------------------------------------------------------

def crs_input_primal(
    dmus: Sequence[str], x: DMUData, y: DMUData
) -> pd.DataFrame:
    """Input-oriented CRS DEA, multiplier (primal) form."""
    n_in, n_out = _validate_shapes(dmus, x, y)
    rows: List[Tuple[str, float]] = []
    for r in dmus:
        prob = LpProblem(f"CRS_in_primal_{r}", LpMaximize)
        v = [LpVariable(f"v_{i}", lowBound=0) for i in range(n_in)]
        u = [LpVariable(f"u_{j}", lowBound=0) for j in range(n_out)]
        prob += lpSum(u[j] * y[r][j] for j in range(n_out))
        prob += lpSum(v[i] * x[r][i] for i in range(n_in)) == 1
        for k in dmus:
            prob += (
                lpSum(u[j] * y[k][j] for j in range(n_out))
                - lpSum(v[i] * x[k][i] for i in range(n_in))
                <= 0
            )
        rows.append((r, _solve_or_raise(prob, r)))
    return _result_frame(rows)


def crs_input_dual(
    dmus: Sequence[str], x: DMUData, y: DMUData
) -> pd.DataFrame:
    """Input-oriented CRS DEA, envelopment (dual) form."""
    n_in, n_out = _validate_shapes(dmus, x, y)
    rows: List[Tuple[str, float]] = []
    for r in dmus:
        prob = LpProblem(f"CRS_in_dual_{r}", LpMinimize)
        lam = {k: LpVariable(f"lam_{k}", lowBound=0) for k in dmus}
        theta = LpVariable(f"theta_{r}")  # free
        prob += theta
        for i in range(n_in):
            prob += lpSum(lam[k] * x[k][i] for k in dmus) <= theta * x[r][i]
        for j in range(n_out):
            prob += lpSum(lam[k] * y[k][j] for k in dmus) >= y[r][j]
        rows.append((r, _solve_or_raise(prob, r)))
    return _result_frame(rows)


def crs_output_primal(
    dmus: Sequence[str], x: DMUData, y: DMUData
) -> pd.DataFrame:
    """Output-oriented CRS DEA, multiplier (primal) form.

    Efficiency is reported as ``1 / objective`` so that values lie in
    ``(0, 1]``.
    """
    n_in, n_out = _validate_shapes(dmus, x, y)
    rows: List[Tuple[str, float]] = []
    for r in dmus:
        prob = LpProblem(f"CRS_out_primal_{r}", LpMinimize)
        v = [LpVariable(f"v_{i}", lowBound=0) for i in range(n_in)]
        u = [LpVariable(f"u_{j}", lowBound=0) for j in range(n_out)]
        prob += lpSum(v[i] * x[r][i] for i in range(n_in))
        prob += lpSum(u[j] * y[r][j] for j in range(n_out)) == 1
        for k in dmus:
            prob += (
                lpSum(v[i] * x[k][i] for i in range(n_in))
                - lpSum(u[j] * y[k][j] for j in range(n_out))
                >= 0
            )
        obj = _solve_or_raise(prob, r)
        rows.append((r, 1.0 / obj if obj else float("inf")))
    return _result_frame(rows)


def crs_output_dual(
    dmus: Sequence[str], x: DMUData, y: DMUData
) -> pd.DataFrame:
    """Output-oriented CRS DEA, envelopment (dual) form.

    Efficiency is reported as ``1 / objective`` so that values lie in
    ``(0, 1]``.
    """
    n_in, n_out = _validate_shapes(dmus, x, y)
    rows: List[Tuple[str, float]] = []
    for r in dmus:
        prob = LpProblem(f"CRS_out_dual_{r}", LpMaximize)
        lam = {k: LpVariable(f"lam_{k}", lowBound=0) for k in dmus}
        phi = LpVariable(f"phi_{r}")  # free
        prob += phi
        for j in range(n_out):
            prob += lpSum(lam[k] * y[k][j] for k in dmus) >= phi * y[r][j]
        for i in range(n_in):
            prob += lpSum(lam[k] * x[k][i] for k in dmus) <= x[r][i]
        obj = _solve_or_raise(prob, r)
        rows.append((r, 1.0 / obj if obj else float("inf")))
    return _result_frame(rows)


# ---------------------------------------------------------------------------
# VRS (Banker-Charnes-Cooper) models
# ---------------------------------------------------------------------------

def vrs_input_primal(
    dmus: Sequence[str], x: DMUData, y: DMUData
) -> pd.DataFrame:
    """Input-oriented VRS DEA, multiplier (primal) form."""
    n_in, n_out = _validate_shapes(dmus, x, y)
    rows: List[Tuple[str, float]] = []
    for r in dmus:
        prob = LpProblem(f"VRS_in_primal_{r}", LpMaximize)
        v = [LpVariable(f"v_{i}", lowBound=0) for i in range(n_in)]
        u = [LpVariable(f"u_{j}", lowBound=0) for j in range(n_out)]
        # u0 is theoretically free; bound it generously to keep the LP
        # numerically stable in degenerate cases. The bound is large enough
        # not to bind in any realistic problem.
        u0 = LpVariable(f"u0_{r}", lowBound=-_FREE_BOUND, upBound=_FREE_BOUND)
        prob += lpSum(u[j] * y[r][j] for j in range(n_out)) - u0
        prob += lpSum(v[i] * x[r][i] for i in range(n_in)) == 1
        for k in dmus:
            prob += (
                lpSum(u[j] * y[k][j] for j in range(n_out))
                - lpSum(v[i] * x[k][i] for i in range(n_in))
                - u0
                <= 0
            )
        rows.append((r, _solve_or_raise(prob, r)))
    return _result_frame(rows)


def vrs_input_dual(
    dmus: Sequence[str], x: DMUData, y: DMUData
) -> pd.DataFrame:
    """Input-oriented VRS DEA, envelopment (dual) form."""
    n_in, n_out = _validate_shapes(dmus, x, y)
    rows: List[Tuple[str, float]] = []
    for r in dmus:
        prob = LpProblem(f"VRS_in_dual_{r}", LpMinimize)
        lam = {k: LpVariable(f"lam_{k}", lowBound=0) for k in dmus}
        theta = LpVariable(f"theta_{r}")
        prob += theta
        for i in range(n_in):
            prob += lpSum(lam[k] * x[k][i] for k in dmus) <= theta * x[r][i]
        for j in range(n_out):
            prob += lpSum(lam[k] * y[k][j] for k in dmus) >= y[r][j]
        prob += lpSum(lam[k] for k in dmus) == 1  # VRS convexity
        rows.append((r, _solve_or_raise(prob, r)))
    return _result_frame(rows)


def vrs_output_primal(
    dmus: Sequence[str], x: DMUData, y: DMUData
) -> pd.DataFrame:
    """Output-oriented VRS DEA, multiplier (primal) form.

    Efficiency is reported as ``1 / objective`` so that values lie in
    ``(0, 1]``.
    """
    n_in, n_out = _validate_shapes(dmus, x, y)
    rows: List[Tuple[str, float]] = []
    for r in dmus:
        prob = LpProblem(f"VRS_out_primal_{r}", LpMinimize)
        v = [LpVariable(f"v_{i}", lowBound=0) for i in range(n_in)]
        u = [LpVariable(f"u_{j}", lowBound=0) for j in range(n_out)]
        # v0 is theoretically free; see comment on u0 in vrs_input_primal.
        v0 = LpVariable(f"v0_{r}", lowBound=-_FREE_BOUND, upBound=_FREE_BOUND)
        prob += lpSum(v[i] * x[r][i] for i in range(n_in)) + v0
        prob += lpSum(u[j] * y[r][j] for j in range(n_out)) == 1
        for k in dmus:
            prob += (
                lpSum(v[i] * x[k][i] for i in range(n_in))
                - lpSum(u[j] * y[k][j] for j in range(n_out))
                + v0
                >= 0
            )
        obj = _solve_or_raise(prob, r)
        rows.append((r, 1.0 / obj if obj else float("inf")))
    return _result_frame(rows)


def vrs_output_dual(
    dmus: Sequence[str], x: DMUData, y: DMUData
) -> pd.DataFrame:
    """Output-oriented VRS DEA, envelopment (dual) form.

    Efficiency is reported as ``1 / objective`` so that values lie in
    ``(0, 1]``.
    """
    n_in, n_out = _validate_shapes(dmus, x, y)
    rows: List[Tuple[str, float]] = []
    for r in dmus:
        prob = LpProblem(f"VRS_out_dual_{r}", LpMaximize)
        lam = {k: LpVariable(f"lam_{k}", lowBound=0) for k in dmus}
        phi = LpVariable(f"phi_{r}")
        prob += phi
        for j in range(n_out):
            prob += lpSum(lam[k] * y[k][j] for k in dmus) >= phi * y[r][j]
        for i in range(n_in):
            prob += lpSum(lam[k] * x[k][i] for k in dmus) <= x[r][i]
        prob += lpSum(lam[k] for k in dmus) == 1  # VRS convexity
        obj = _solve_or_raise(prob, r)
        rows.append((r, 1.0 / obj if obj else float("inf")))
    return _result_frame(rows)


# ---------------------------------------------------------------------------
# Back-compatible dispatchers
# ---------------------------------------------------------------------------

_CRS_DISPATCH = {
    ("input", False): crs_input_primal,
    ("input", True): crs_input_dual,
    ("output", False): crs_output_primal,
    ("output", True): crs_output_dual,
}

_VRS_DISPATCH = {
    ("input", False): vrs_input_primal,
    ("input", True): vrs_input_dual,
    ("output", False): vrs_output_primal,
    ("output", True): vrs_output_dual,
}


def CRS(  # noqa: N802 - keep historical capitalisation for API compatibility
    DMU: Sequence[str],
    X: DMUData,
    Y: DMUData,
    orientation: str,
    dual: bool,
) -> pd.DataFrame:
    """Backward-compatible CRS dispatcher.

    Parameters
    ----------
    DMU : Sequence[str]
        Ordered DMU identifiers.
    X, Y : DMUData
        Input and output dictionaries keyed by DMU.
    orientation : {'input', 'output'}
    dual : bool
        If True, the envelopment (dual) form is solved; otherwise the
        multiplier (primal) form is solved.

    Returns
    -------
    pandas.DataFrame
        Columns ``['DMU', 'efficiency']``.
    """
    key = (str(orientation).lower(), bool(dual))
    if key not in _CRS_DISPATCH:
        raise ValueError(
            f"Unknown CRS combination orientation={orientation!r}, "
            f"dual={dual!r}."
        )
    return _CRS_DISPATCH[key](DMU, X, Y)


def VRS(  # noqa: N802 - keep historical capitalisation for API compatibility
    DMU: Sequence[str],
    X: DMUData,
    Y: DMUData,
    orientation: str,
    dual: bool,
) -> pd.DataFrame:
    """Backward-compatible VRS dispatcher.

    See :func:`CRS` for parameter semantics.
    """
    key = (str(orientation).lower(), bool(dual))
    if key not in _VRS_DISPATCH:
        raise ValueError(
            f"Unknown VRS combination orientation={orientation!r}, "
            f"dual={dual!r}."
        )
    return _VRS_DISPATCH[key](DMU, X, Y)


__all__ = [
    "CRS",
    "VRS",
    "crs_input_primal",
    "crs_input_dual",
    "crs_output_primal",
    "crs_output_dual",
    "vrs_input_primal",
    "vrs_input_dual",
    "vrs_output_primal",
    "vrs_output_dual",
]
