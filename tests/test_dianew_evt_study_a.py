"""Tests for the dependency-light parts of the DIANEW Study A helpers."""

from __future__ import annotations

import numpy as np
import pytest

from experimental.dianew_evt_study_a import (
    EVTProtocolError,
    decluster_exceedances,
    finite_right_endpoint,
)


def test_decluster_exceedances_retains_one_maximum_per_cluster() -> None:
    values = [0.0, 1.1, 1.4, 0.2, 1.2, 0.1, 1.3, 1.8, 0.0]

    peaks = decluster_exceedances(values, threshold=1.0, run_length=1)

    assert np.allclose(peaks, [1.4, 1.2, 1.8])


def test_decluster_exceedances_can_join_short_gaps() -> None:
    values = [0.0, 1.1, 0.2, 1.5, 0.0]

    peaks = decluster_exceedances(values, threshold=1.0, run_length=2)

    assert np.allclose(peaks, [1.5])


def test_negative_shape_has_finite_conditional_endpoint() -> None:
    assert finite_right_endpoint(threshold=10.0, shape_xi=-0.5, scale_beta=2.0) == 14.0


def test_nonnegative_shape_has_no_finite_endpoint() -> None:
    assert finite_right_endpoint(threshold=10.0, shape_xi=0.0, scale_beta=2.0) is None
    assert finite_right_endpoint(threshold=10.0, shape_xi=0.2, scale_beta=2.0) is None


def test_protocol_rejects_invalid_inputs() -> None:
    with pytest.raises(EVTProtocolError, match="run_length"):
        decluster_exceedances([1.0, 2.0], threshold=1.5, run_length=0)

    with pytest.raises(EVTProtocolError, match="strictly positive"):
        finite_right_endpoint(threshold=1.0, shape_xi=-0.1, scale_beta=0.0)
