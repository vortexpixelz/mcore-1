"""DIANEW / NS-001 Study A — declustered POT analysis helpers.

This module supports a falsification-safe *empirical* workflow for tail statistics of
an explicitly declared vorticity-extreme observable. It is not a CFD solver, a
Navier–Stokes proof, or evidence of singularity / regularity on its own.

The central protection here is dependence awareness: sequential DNS outputs are
correlated, so every exceedance above a threshold must not be treated as an
independent draw. `decluster_exceedances` retains one peak per run-declustered
cluster before fitting a generalized Pareto distribution (GPD).

Requires the repository's ``analysis`` extra for SciPy:

    uv sync --extra analysis
    uv run python experimental/dianew_evt_study_a.py --demo
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np


class EVTProtocolError(ValueError):
    """Raised when input data violate the minimal Study A protocol contract."""


@dataclass(frozen=True)
class GPDThresholdFit:
    """A fitted declustered POT model at one threshold.

    `endpoint` is populated only for a negative GPD shape. It is a conditional
    model estimate, not a physical upper bound.
    """

    threshold: float
    n_raw_exceedances: int
    n_cluster_peaks: int
    shape_xi: float
    scale_beta: float
    endpoint: float | None


@dataclass(frozen=True)
class BootstrapShapeInterval:
    """Nonparametric bootstrap summary for a GPD shape estimate."""

    point_estimate: float
    lower: float
    upper: float
    successful_resamples: int
    requested_resamples: int


def _finite_vector(values: Iterable[float], *, name: str = "values") -> np.ndarray:
    """Return a one-dimensional finite float vector or raise a clear protocol error."""

    array = np.asarray(list(values), dtype=float)
    if array.ndim != 1:
        raise EVTProtocolError(f"{name} must be one-dimensional; got shape {array.shape}.")
    if array.size == 0:
        raise EVTProtocolError(f"{name} must contain at least one observation.")
    if not np.isfinite(array).all():
        raise EVTProtocolError(f"{name} contains NaN or infinite values.")
    return array


def decluster_exceedances(
    values: Iterable[float],
    threshold: float,
    *,
    run_length: int = 1,
) -> np.ndarray:
    """Return the maximum observation from each sequential exceedance cluster.

    Parameters
    ----------
    values:
        Time-ordered scalar observations, e.g. a declared ``omega_max(t)`` series.
    threshold:
        Strict exceedance threshold. Observations equal to the threshold are not
        exceedances.
    run_length:
        Maximum index gap that still joins two exceedances into the same cluster.
        A value of one means consecutive exceedances are grouped. The choice must
        be justified from output cadence / correlation diagnostics in a real study.
    """

    series = _finite_vector(values)
    if not np.isfinite(threshold):
        raise EVTProtocolError("threshold must be finite.")
    if run_length < 1:
        raise EVTProtocolError("run_length must be at least 1.")

    exceedance_indices = np.flatnonzero(series > threshold)
    if exceedance_indices.size == 0:
        return np.array([], dtype=float)

    clusters: list[list[int]] = [[int(exceedance_indices[0])]]
    for raw_index in exceedance_indices[1:]:
        index = int(raw_index)
        if index - clusters[-1][-1] <= run_length:
            clusters[-1].append(index)
        else:
            clusters.append([index])

    return np.asarray([float(np.max(series[cluster])) for cluster in clusters], dtype=float)


def finite_right_endpoint(
    threshold: float,
    shape_xi: float,
    scale_beta: float,
    *,
    near_zero: float = 1e-12,
) -> float | None:
    """Compute the GPD right endpoint when shape is meaningfully negative.

    The endpoint is ``u - beta / xi`` for ``xi < 0``. A near-zero shape is treated
    as an unbounded exponential-domain limit, avoiding numerical theater around
    division by a tiny coefficient.
    """

    if not np.isfinite([threshold, shape_xi, scale_beta]).all():
        raise EVTProtocolError("threshold, shape_xi, and scale_beta must be finite.")
    if scale_beta <= 0:
        raise EVTProtocolError("scale_beta must be strictly positive.")
    if shape_xi >= -near_zero:
        return None
    return float(threshold - (scale_beta / shape_xi))


def fit_gpd_threshold(
    values: Iterable[float],
    threshold: float,
    *,
    run_length: int = 1,
    min_cluster_peaks: int = 50,
) -> GPDThresholdFit:
    """Fit a GPD to declustered exceedance peaks at one fixed threshold.

    SciPy's location is fixed at zero because the fitted sample consists of excesses
    ``peak - threshold``. This makes the parameterization auditable.
    """

    if min_cluster_peaks < 3:
        raise EVTProtocolError("min_cluster_peaks must be at least 3.")

    series = _finite_vector(values)
    raw_count = int(np.count_nonzero(series > threshold))
    peaks = decluster_exceedances(series, threshold, run_length=run_length)
    if peaks.size < min_cluster_peaks:
        raise EVTProtocolError(
            "Insufficient declustered exceedance peaks for a GPD fit: "
            f"got {peaks.size}, require {min_cluster_peaks}."
        )

    try:
        from scipy.stats import genpareto
    except ImportError as exc:  # pragma: no cover - environment-dependent
        raise RuntimeError(
            "SciPy is required for GPD fitting. Install the analysis extra: "
            "uv sync --extra analysis"
        ) from exc

    excesses = peaks - threshold
    shape_xi, location, scale_beta = genpareto.fit(excesses, floc=0.0)
    if not np.isclose(location, 0.0):  # Defensive: `floc` should guarantee this.
        raise RuntimeError("Unexpected nonzero GPD location after fixed-location fit.")

    endpoint = finite_right_endpoint(float(threshold), float(shape_xi), float(scale_beta))
    return GPDThresholdFit(
        threshold=float(threshold),
        n_raw_exceedances=raw_count,
        n_cluster_peaks=int(peaks.size),
        shape_xi=float(shape_xi),
        scale_beta=float(scale_beta),
        endpoint=endpoint,
    )


def fit_threshold_grid(
    values: Iterable[float],
    quantiles: Sequence[float] = (0.90, 0.925, 0.95, 0.975),
    *,
    run_length: int = 1,
    min_cluster_peaks: int = 50,
) -> list[GPDThresholdFit]:
    """Fit the preregistered threshold grid, retaining each successful fit.

    The function deliberately does not silently choose a flattering threshold. It
    returns fits in the caller's supplied order. Thresholds with too few clusters
    raise a protocol error that names the failed threshold.
    """

    series = _finite_vector(values)
    if not quantiles:
        raise EVTProtocolError("quantiles must not be empty.")
    if any(not 0.0 < q < 1.0 for q in quantiles):
        raise EVTProtocolError("every threshold quantile must lie strictly between 0 and 1.")

    fits: list[GPDThresholdFit] = []
    for quantile in quantiles:
        threshold = float(np.quantile(series, quantile))
        fits.append(
            fit_gpd_threshold(
                series,
                threshold,
                run_length=run_length,
                min_cluster_peaks=min_cluster_peaks,
            )
        )
    return fits


def bootstrap_shape_interval(
    values: Iterable[float],
    threshold: float,
    *,
    run_length: int = 1,
    n_resamples: int = 500,
    confidence: float = 0.95,
    seed: int = 0,
    min_cluster_peaks: int = 50,
) -> BootstrapShapeInterval:
    """Bootstrap the GPD shape from declustered cluster maxima.

    Resampling occurs at the cluster-peak level, not the raw time-step level. This
    does not prove independence; it only avoids the most obvious pseudo-replication.
    Report the chosen run length and effective peak count alongside the interval.
    """

    if n_resamples < 20:
        raise EVTProtocolError("n_resamples must be at least 20 for a useful interval.")
    if not 0.0 < confidence < 1.0:
        raise EVTProtocolError("confidence must lie strictly between 0 and 1.")

    point_fit = fit_gpd_threshold(
        values,
        threshold,
        run_length=run_length,
        min_cluster_peaks=min_cluster_peaks,
    )
    peaks = decluster_exceedances(values, threshold, run_length=run_length)
    excesses = peaks - threshold

    try:
        from scipy.stats import genpareto
    except ImportError as exc:  # pragma: no cover - environment-dependent
        raise RuntimeError(
            "SciPy is required for bootstrap GPD fitting. Install the analysis extra: "
            "uv sync --extra analysis"
        ) from exc

    rng = np.random.default_rng(seed)
    shapes: list[float] = []
    for _ in range(n_resamples):
        sample = rng.choice(excesses, size=excesses.size, replace=True)
        try:
            shape_xi, _, _ = genpareto.fit(sample, floc=0.0)
        except (FloatingPointError, ValueError):
            continue
        if np.isfinite(shape_xi):
            shapes.append(float(shape_xi))

    if len(shapes) < max(20, int(n_resamples * 0.8)):
        raise EVTProtocolError(
            "Too many bootstrap fits failed; inspect threshold, numerical stability, "
            "or sample size before reporting an interval."
        )

    tail_probability = (1.0 - confidence) / 2.0
    lower, upper = np.quantile(shapes, [tail_probability, 1.0 - tail_probability])
    return BootstrapShapeInterval(
        point_estimate=point_fit.shape_xi,
        lower=float(lower),
        upper=float(upper),
        successful_resamples=len(shapes),
        requested_resamples=n_resamples,
    )


def _demo_series(seed: int = 7, n: int = 10_000) -> np.ndarray:
    """Create a correlated bounded-support control for CLI smoke testing only."""

    rng = np.random.default_rng(seed)
    innovations = rng.beta(2.0, 5.0, size=n)
    series = np.empty(n, dtype=float)
    series[0] = innovations[0]
    for index in range(1, n):
        series[index] = 0.85 * series[index - 1] + 0.15 * innovations[index]
    return series


def _print_demo() -> None:
    series = _demo_series()
    threshold = float(np.quantile(series, 0.95))
    fit = fit_gpd_threshold(series, threshold, run_length=5, min_cluster_peaks=50)
    interval = bootstrap_shape_interval(
        series,
        threshold,
        run_length=5,
        n_resamples=200,
        seed=7,
        min_cluster_peaks=50,
    )

    print("DIANEW / NS-001 Study A synthetic-control demo")
    print("This is a bounded, correlated toy series. It is not DNS evidence.")
    print(f"threshold: {fit.threshold:.6f}")
    print(f"raw exceedances: {fit.n_raw_exceedances}")
    print(f"declustered peaks: {fit.n_cluster_peaks}")
    print(f"GPD shape xi: {fit.shape_xi:.4f}")
    print(f"bootstrap {interval.successful_resamples}/{interval.requested_resamples} "
          f"shape CI: [{interval.lower:.4f}, {interval.upper:.4f}]")
    print(f"conditional fitted endpoint: {fit.endpoint}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run the DIANEW Study A synthetic EVT control.")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="run the bounded correlated synthetic-control demonstration",
    )
    args = parser.parse_args()
    if args.demo:
        _print_demo()
    else:
        parser.print_help()
