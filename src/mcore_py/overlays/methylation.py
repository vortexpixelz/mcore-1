"""
MethylationMetrics Overlay — MCORE-1 (Domain 02 Extension)
===========================================================

Extends MCORE-1 for CpG methylation analysis. The mapping is exact:
DNA methylation is natively ternary — the only biological domain that maps
to {S1, S2, S3} without forcing a quaternary alphabet into three bins.

    Unmethylated CpG    ->  Trit S1  (open, accessible)
    Hemimethylated CpG  ->  Trit S2  (post-replication intermediate)
    Fully methylated    ->  Trit S3  (silenced, stable)

Conservation law: a CpG island budget constrains how many S3 (fully
methylated) sites a regulatory region can carry. Hypermethylation of
tumor suppressor genes = S3 overflow -> check_tree() returns invalid.

Hierarchy:
    L0  cpg_site         one CpG dinucleotide
    L1  cpg_cluster      local run of CpG sites (3-5 bp window)
    L2  cpg_island       regulatory island (check_tree() validated)
    L3  promoter_region  one gene's promoter
    L4  locus            genomic locus / gene body
"""

from __future__ import annotations

from enum import Enum, auto
from typing import Sequence

from mcore_py.model import (
    Budget,
    Constituent,
    HierarchyMap,
    Level,
    ProsodicUnit,
    Tension,
    Trit,
)


# ---------------------------------------------------------------------------
# Methylation state thresholds
# ---------------------------------------------------------------------------

BETA_UNMETHYLATED_MAX: float = 0.20   # beta < 0.20  -> UNMETHYLATED (S1)
BETA_HEMIMETHYLATED_MAX: float = 0.80  # beta < 0.80  -> HEMIMETHYLATED (S2)
                                        # beta >= 0.80 -> FULLY_METHYLATED (S3)


# ---------------------------------------------------------------------------
# Methylation state enum
# ---------------------------------------------------------------------------

class MethylationState(Enum):
    """Ternary CpG methylation state.

    Maps directly onto MCORE-1 trit values:
        UNMETHYLATED    ->  Trit.S1  beta < 0.20
        HEMIMETHYLATED  ->  Trit.S2  0.20 <= beta < 0.80
        FULLY_METHYLATED->  Trit.S3  beta >= 0.80

    The hemimethylated state (S2) arises naturally after DNA replication:
    the template strand is methylated, the newly synthesized strand is not.
    DNMT1 resolves this to S3; failure to do so is a driver of epigenetic
    instability in cancer.
    """
    UNMETHYLATED = auto()      # Open chromatin, gene expression permitted
    HEMIMETHYLATED = auto()    # Post-replication intermediate, transitional
    FULLY_METHYLATED = auto()  # Silenced; stable if intentional, oncogenic if aberrant


METHYLATION_WEIGHT_MAP: dict[MethylationState, Trit] = {
    MethylationState.UNMETHYLATED:     Trit.S1,
    MethylationState.HEMIMETHYLATED:   Trit.S2,
    MethylationState.FULLY_METHYLATED: Trit.S3,
}


def classify_cpg(beta: float) -> MethylationState:
    """Classify a CpG site from its beta value (methylation fraction).

    Parameters
    ----------
    beta : float
        Methylation fraction in [0.0, 1.0]. 0 = unmethylated, 1 = fully
        methylated. Typically from bisulfite sequencing (WGBS/RRBS) or
        methylation array (Illumina 450K/EPIC).

    Returns
    -------
    MethylationState
        Ternary methylation state.

    Raises
    ------
    ValueError
        If beta is outside [0.0, 1.0].

    Examples
    --------
    >>> classify_cpg(0.05)
    <MethylationState.UNMETHYLATED: 1>
    >>> classify_cpg(0.50)
    <MethylationState.HEMIMETHYLATED: 2>
    >>> classify_cpg(0.92)
    <MethylationState.FULLY_METHYLATED: 3>
    """
    if not 0.0 <= beta <= 1.0:
        raise ValueError(f"beta must be in [0.0, 1.0], got {beta}")
    if beta < BETA_UNMETHYLATED_MAX:
        return MethylationState.UNMETHYLATED
    if beta < BETA_HEMIMETHYLATED_MAX:
        return MethylationState.HEMIMETHYLATED
    return MethylationState.FULLY_METHYLATED


def cpg_weight(state: MethylationState) -> Trit:
    """Return the Trit weight for a methylation state."""
    return METHYLATION_WEIGHT_MAP[state]


# ---------------------------------------------------------------------------
# Hierarchy map — methylation terminology aliases
# ---------------------------------------------------------------------------

METHYLATION_HIERARCHY: HierarchyMap = HierarchyMap(
    aliases={
        Level.L0_MATRA:  ("cpg_site",        "CpG site"),
        Level.L1_AKSARA: ("cpg_cluster",      "CpG cluster"),
        Level.L2_GANA:   ("cpg_island",       "CpG island"),
        Level.L3_PADA:   ("promoter_region",  "promoter region"),
        Level.L4_SLOKA:  ("locus",            "locus"),
    }
)


# ---------------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------------

def cpg_site(
    beta: float,
    label: str | None = None,
    tension: Tension = Tension.NEUTRAL,
) -> ProsodicUnit:
    """Create a ProsodicUnit representing one CpG site (L0: cpg_site).

    Parameters
    ----------
    beta : float
        Methylation fraction in [0.0, 1.0].
    label : str | None
        Optional site identifier (e.g. 'cg00000029', 'chr17:7674220').
    tension : Tension
        Tension state for tracking aberrant methylation displacement.

    Returns
    -------
    ProsodicUnit
        At Level.L0_MATRA (CpG site), weight derived from beta.
    """
    state = classify_cpg(beta)
    return ProsodicUnit(
        weight=cpg_weight(state),
        tension=tension,
        level=Level.L0_MATRA,
        label=label,
        features={"beta": beta, "methylation_state": state.name},
    )


def cpg_cluster(
    *sites: ProsodicUnit,
    label: str | None = None,
) -> tuple[ProsodicUnit, list[ProsodicUnit]]:
    """Create a CpG cluster (L1) from individual CpG sites.

    A cluster is a local run of CpG dinucleotides. The pooled weight
    represents the methylation burden of the window. Overflow indicates
    hypermethylation beyond the S3 budget — a flag for aberrant silencing.

    Parameters
    ----------
    *sites : ProsodicUnit
        CpG site ProsodicUnits (L0_MATRA).
    label : str | None
        Optional cluster label.

    Returns
    -------
    tuple[ProsodicUnit, list[ProsodicUnit]]
        Parent unit at L1_AKSARA and ordered child list.

    Raises
    ------
    ValueError
        If combined methylation weights overflow S3.
    """
    from mcore_py.algebra import OVERFLOW, trit_add_seq

    weights = [s.weight for s in sites]
    pooled = trit_add_seq(list(weights))

    if pooled is OVERFLOW:
        raise ValueError(
            f"CpG cluster overflow: site weights {[w.name for w in weights]} "
            f"exceed S3 budget. Hypermethylation detected — split cluster or "
            f"flag as aberrant."
        )

    parent = ProsodicUnit(
        weight=pooled,
        level=Level.L1_AKSARA,
        label=label,
        features={"cpg_count": len(sites)},
    )
    return parent, list(sites)


def cpg_island(
    *clusters: tuple[ProsodicUnit, list[ProsodicUnit]],
    budget: Budget | None = None,
    label: str | None = None,
) -> Constituent:
    """Build a CpG island (L2) from CpG clusters.

    A CpG island is a regulatory region where check_tree() enforces the
    methylation conservation budget. Well-formed islands have balanced
    methylation patterns; tumor suppressor gene silencing manifests as
    budget overflow.

    Parameters
    ----------
    *clusters : tuple[ProsodicUnit, list[ProsodicUnit]]
        CpG clusters as returned by cpg_cluster().
    budget : Budget | None
        Optional methylation budget. If None, only conservation law
        is enforced by check_tree().
    label : str | None
        Optional island label (e.g. gene name, genomic coordinates).

    Returns
    -------
    Constituent
        A complete L2 Constituent ready for check_tree() validation.

    Raises
    ------
    ValueError
        If no clusters provided, or combined weights exceed S3.
    """
    from mcore_py.algebra import OVERFLOW, trit_add_seq

    if not clusters:
        raise ValueError("cpg_island requires at least one CpG cluster.")

    cluster_parents = [c[0] for c in clusters]
    cluster_weights = [p.weight for p in cluster_parents]
    pooled = trit_add_seq(cluster_weights)

    if pooled is OVERFLOW:
        raise ValueError(
            f"CpG island overflow: cluster weights "
            f"{[w.name for w in cluster_weights]} exceed S3. "
            f"Aberrant hypermethylation — flag for oncological review."
        )

    island_parent = ProsodicUnit(
        weight=pooled,
        level=Level.L2_GANA,
        label=label,
        features={"cluster_count": len(clusters)},
    )

    children: list[Constituent] = [
        Constituent(parent=cluster_parent, children=list(cluster_sites))
        for cluster_parent, cluster_sites in clusters
    ]

    return Constituent(
        parent=island_parent,
        children=children,
        budget=budget,
    )


# ---------------------------------------------------------------------------
# High-level overlay class
# ---------------------------------------------------------------------------

class MethylationMetrics:
    """Overlay for CpG methylation analysis using MCORE-1 conservation.

    The only biological domain that maps natively to {S1, S2, S3} without
    forcing a non-ternary alphabet into three bins. DNA methylation has
    exactly three functional states at each CpG site, and the conservation
    constraint (CpG island budget) is a real biological phenomenon:
    aberrant hypermethylation of tumor suppressor promoters is a hallmark
    of cancer.

    check_tree() validates methylation patterns the same way it validates
    Sanskrit metrical feet and quantum scheduling frames — same conservation
    law, same function, different domain.

    Hierarchy:
        L0  cpg_site         one CpG dinucleotide (beta value)
        L1  cpg_cluster      local CpG window
        L2  cpg_island       regulatory island (check_tree() validated)
        L3  promoter_region  gene promoter
        L4  locus            genomic locus
    """

    HIERARCHY: HierarchyMap = METHYLATION_HIERARCHY

    @staticmethod
    def site(
        beta: float,
        label: str | None = None,
        tension: Tension = Tension.NEUTRAL,
    ) -> ProsodicUnit:
        """Create a CpG site from a beta value."""
        return cpg_site(beta, label=label, tension=tension)

    @staticmethod
    def cluster(
        *sites: ProsodicUnit,
        label: str | None = None,
    ) -> tuple[ProsodicUnit, list[ProsodicUnit]]:
        """Create a CpG cluster from sites."""
        return cpg_cluster(*sites, label=label)

    @staticmethod
    def island(
        *clusters: tuple[ProsodicUnit, list[ProsodicUnit]],
        budget: Budget | None = None,
        label: str | None = None,
    ) -> Constituent:
        """Build a CpG island from clusters."""
        return cpg_island(*clusters, budget=budget, label=label)

    @staticmethod
    def from_beta_list(
        betas: Sequence[float],
        labels: Sequence[str] | None = None,
        budget: Budget | None = None,
        island_label: str | None = None,
    ) -> Constituent:
        """Build a CpG island directly from a list of beta values.

        Each beta value becomes one CpG site in its own cluster, all
        collected into a single island. Convenient for feeding raw
        bisulfite sequencing output directly into check_tree().

        Parameters
        ----------
        betas : Sequence[float]
            Per-site methylation fractions in [0.0, 1.0].
        labels : Sequence[str] | None
            Optional CpG site labels. Must match len(betas) if provided.
        budget : Budget | None
            Optional methylation budget for the island.
        island_label : str | None
            Optional label for the island (e.g. gene name).

        Returns
        -------
        Constituent
            A CpG island ready for check_tree() validation.

        Examples
        --------
        >>> from mcore_py.checker import check_tree
        >>> island = MethylationMetrics.from_beta_list([0.05, 0.50])
        >>> check_tree(island).valid
        True
        """
        if labels is not None and len(labels) != len(betas):
            raise ValueError(
                f"labels length {len(labels)} != betas length {len(betas)}"
            )

        clusters = []
        for i, b in enumerate(betas):
            lbl = labels[i] if labels is not None else f"cg{i:04d}"
            s = cpg_site(b, label=lbl)
            clusters.append(cpg_cluster(s, label=f"cluster_{lbl}"))

        return cpg_island(*clusters, budget=budget, label=island_label)

    @staticmethod
    def decoherence_trajectory(
        initial_betas: Sequence[float],
        drift_rate: float = 0.05,
        steps: int = 5,
    ) -> list[list[MethylationState]]:
        """Model epigenetic drift as a ternary state trajectory.

        Simulates progressive hypermethylation (drift toward S3) under
        oncogenic pressure, or hypomethylation (drift toward S1) under
        demethylase activity. The direction is determined by drift_rate
        sign convention: positive = methylation gain (cancer progression),
        negative = methylation loss (global hypomethylation).

        Parameters
        ----------
        initial_betas : Sequence[float]
            Starting beta values for each CpG site in [0.0, 1.0].
        drift_rate : float
            Beta change per step. Positive = hypermethylation pressure.
        steps : int
            Number of time steps to simulate.

        Returns
        -------
        list[list[MethylationState]]
            Outer list = time steps, inner list = per-site MethylationState.
        """
        trajectory: list[list[MethylationState]] = []
        current = list(initial_betas)

        for _ in range(steps):
            snapshot = [classify_cpg(max(0.0, min(1.0, b))) for b in current]
            trajectory.append(snapshot)
            current = [max(0.0, min(1.0, b + drift_rate)) for b in current]

        return trajectory
