# DIANEW / NS-001 — Study A: Extreme-Value Protocol

**Status:** research protocol and software scaffolding  
**Project role:** falsification-safe empirical study  
**Scope boundary:** this document does **not** claim a Navier–Stokes proof, a singularity, or a universal physical endpoint.

## 1. Research question

Can a carefully declustered peaks-over-threshold (POT) analysis of a vorticity-extreme observable in statistically stationary DNS distinguish a bounded-tail regime from an effectively unbounded one?

The primary estimand is the generalized Pareto distribution (GPD) shape parameter, `xi`:

- `xi < 0`: bounded-tail / Weibull-domain evidence at the chosen observable, sampling frame, and threshold range.
- `xi = 0`: exponential-domain behavior.
- `xi > 0`: heavy-tail / Fréchet-domain evidence.

This is an **empirical tail characterization**, not a regularity theorem. A finite fitted endpoint is conditional on data quality, stationarity, declustering, threshold stability, and model adequacy.

## 2. Primary observable and unit of analysis

**Primary observable, provisional:** a time-indexed spatial maximum of vorticity magnitude, `omega_max(t)`, normalized by a declared physical scale such as `tau_K` when the dataset metadata supports it.

**Analysis unit:** declustered exceedance peaks above a threshold `u` rather than every correlated sample above `u`.

The data schema must preserve:

```text
run_id
snapshot_time
block_id / output-cadence metadata
omega_max
normalization metadata (for example tau_K, R_lambda)
spatial location of omega_max, if available
resolution and forcing metadata
```

A single field snapshot is useful for a spatial-tail study but does **not** answer the primary time-series block-maxima/POT question. The first external data gate is therefore time resolution and retention policy, not statistical cleverness.

## 3. Preregistered analysis ladder

### Gate 0 — synthetic controls

Use the included helper module on two synthetic controls before touching DNS:

1. A bounded-support control should recover a negative-shape tendency and a finite endpoint within wide uncertainty.
2. A correlated process should demonstrate why naive sample counts overstate confidence, and why declustering is required.

### Gate 1 — incumbent baseline reproduction

On the same declared variable used in the source literature, reproduce a tail fit compatible with the incumbent stretched-exponential baseline. Do not compare a vorticity-magnitude fit directly to an enstrophy fit without making the variable transformation explicit.

### Gate 2 — declustered POT fitting

For a preregistered threshold grid, fit GPD exceedances using cluster maxima. Record:

- threshold `u`
- run-length / separation rule
- raw and declustered exceedance counts
- shape `xi` and scale `beta`
- bootstrap interval for `xi`
- finite endpoint estimate only when `xi < 0`

### Gate 3 — stability and sensitivity

A result is reportable only if its qualitative conclusion survives a reasonable threshold band and at least two defensible declustering windows. A dramatic estimate at one threshold is a tail mirage until it survives this gate.

### Gate 4 — out-of-sample checks

Hold out contiguous time blocks. Fit on the training blocks and evaluate tail probability calibration on held-out blocks. The GPD is a candidate model, not a ceremonial costume.

## 4. Falsification rules

The flagship hypothesis is **not** "Navier–Stokes is regular." It is deliberately narrower:

> In a specified stationary DNS dataset and specified observable, declustered POT exceedances are better described by a bounded-tail GPD than by an effectively unbounded alternative, with a stable negative shape estimate across the preregistered sensitivity grid.

Null / negative outcomes are first-class:

- `xi >= 0` or confidence intervals that materially span zero.
- No threshold-stable estimate.
- Endpoint estimates that move wildly across threshold or run-length choices.
- The stretched-exponential baseline matches or outperforms the GPD under held-out evaluation.
- Available data lack time resolution sufficient for declustering.

Any of these outcomes means: **no bounded-tail conclusion from this dataset.** They do not imply a singularity, and they do not establish global regularity.

## 5. Claim ledger

| Tier | Permitted statement |
|---|---|
| **ESTABLISHED** | EVT supplies asymptotic models for maxima/exceedances under assumptions that must be checked or approximated. |
| **ESTABLISHED** | Turbulence output is temporally correlated; effective sample size cannot be equated with raw sample count. |
| **PLAUSIBLE / TESTABLE** | A declustered GPD may offer a useful complementary tail summary to stretched-exponential fits. |
| **CONJECTURAL** | A stable negative `xi` in finite DNS could be interpreted as empirical evidence consistent with finite observed extremes at that regime. |
| **FORBIDDEN PUBLIC CLAIM** | This analysis proves Navier–Stokes regularity or rules out singularity in 3D Navier–Stokes. |

## 6. First work packet

1. **Data feasibility memo:** identify which public datasets provide a time-resolved `omega_max(t)` or raw enough fields to compute it.
2. **Baseline notebook:** reproduce a published tail fit on the exact variable reported.
3. **POT notebook:** use `experimental/dianew_evt_study_a.py` for declustering, threshold-grid fitting, bootstrap intervals, and endpoint bookkeeping.
4. **Method note:** report dependence treatment, threshold selection, resolution limits, and negative results before interpretation.

## 7. Questions for a data owner / DNS expert

The immediate feasibility questions are operational:

1. Is the relevant high-resolution release a single snapshot, regularly spaced time slices, or a retained extrema time series?
2. What output cadence is available relative to the Kolmogorov time scale?
3. Are `omega_max(t)` values, locations, or full-field cutouts accessible without reconstructing an entire DNS pipeline?
4. Which normalization and resolution-quality metadata should accompany any tail analysis?
5. Is there an existing stationary interval that should be treated as the canonical analysis window?

## 8. Relation to the broader NS-001 lane

This protocol is intentionally separated from the Gabor–Hölder toy diagnostic in issue #28. The toy module is an educational / symbolic regularity-proxy lane. Study A is a data-bound statistical falsification lane. They may share governance conventions, but neither validates the other.
