"""Smoke tests for standalone S3 analysis scripts (optional deps)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _deps_available() -> bool:
    try:
        import numpy  # noqa: F401
        import pandas  # noqa: F401
        import requests  # noqa: F401
        import scipy  # noqa: F401
        import sklearn  # noqa: F401
    except ImportError:
        return False
    return True


@pytest.mark.skipif(not _deps_available(), reason="analysis optional-dependencies not installed")
def test_winner_characterization_runs_no_save() -> None:
    script = ROOT / "S3_Winner_Subset_Characterization.py"
    r = subprocess.run(
        [sys.executable, str(script), "--no-save"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert r.returncode == 0, r.stderr + r.stdout
    assert "STAGE 1" in r.stdout
    assert "STAGE 4" in r.stdout


def test_crystallization_analysis_runs_falsifiable() -> None:
    script = ROOT / "s3_crystallization_analysis.py"
    r = subprocess.run(
        [sys.executable, str(script), "--module", "falsifiable"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert r.returncode == 0, r.stderr + r.stdout
    assert "FALSIFIABLE TEST" in r.stdout
