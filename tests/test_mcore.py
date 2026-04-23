"""
Comprehensive test suite for mcore-py.
Tests organized by spec section.
"""

import argparse
import subprocess

import pytest

from mcore_py.model import (
    Budget, Constituent, EdgeLicense, HierarchyMap,
    Level, ProsodicUnit, Tension, Trit,
)
from mcore_py.algebra import (
    OVERFLOW, complete, enumerate_patterns, project,
    tension_pair, trit_add, trit_add_seq,
)
from mcore_py.checker import CheckResult, ErrorKind, check_tree
from mcore_py.tme6 import (
    Opcode, decode_tme6, encode_tme6, opcodes_to_ints,
)
from mcore_py.base64tme import (
    annotate_stream, from_base64tme, is_metrical_content,
    to_base64tme,
)
from mcore_py.mss import emit_mss, parse_mss, parse_mss_to_units
from mcore_py.renderers.terminal import render_scansion
from mcore_py.renderers.token_stream import (
    MetricalToken, StreamValidator, render_token_stream,
)
from mcore_py.overlays.quantitative_metrics import (
    QuantitativeMetrics, SyllableType, SyncopationType,
    classify_syllable, resolve_heavy,
)
from mcore_py import cli as mcore_cli
from mcore_py.cli import parse_pattern, trits_to_str


# ===================================================================
# §2  Data Model
# ===================================================================

class TestDataModel:
    """Tests for Spec Section 2: MCORE-1 Data Model."""

    def test_trit_values(self):
        assert Trit.S1 == 0
        assert Trit.S2 == 1
        assert Trit.S3 == 2

    def test_tension_values(self):
        assert Tension.DEBT == -1
        assert Tension.NEUTRAL == 0
        assert Tension.SURPLUS == 1

    def test_level_values(self):
        assert Level.L0_MATRA == 0
        assert Level.L4_SLOKA == 4

    def test_prosodic_unit_defaults(self):
        u = ProsodicUnit()
        assert u.weight == Trit.S1
        assert u.tension == Tension.NEUTRAL
        assert u.level == Level.L0_MATRA
        assert u.id  # has a UUID

    def test_prosodic_unit_repr(self):
        u = ProsodicUnit(weight=Trit.S2, tension=Tension.DEBT)
        r = repr(u)
        assert "S2" in r
        assert "-" in r

    def test_budget_satisfied(self):
        b = Budget(min_weight=Trit.S1, max_weight=Trit.S2, unit=Level.L0_MATRA)
        assert b.satisfied(0)
        assert b.satisfied(1)
        assert not b.satisfied(2)

    def test_budget_exact(self):
        b = Budget(min_weight=Trit.S2, max_weight=Trit.S2, exact=True)
        assert not b.satisfied(0)
        assert b.satisfied(1)
        assert not b.satisfied(2)

    def test_hierarchy_map_defaults(self):
        hm = HierarchyMap()
        assert hm.sanskrit(Level.L0_MATRA) == "matra"
        assert hm.english(Level.L2_GANA) == "foot"

    def test_hierarchy_map_from_name(self):
        hm = HierarchyMap()
        assert hm.from_name("mora") == Level.L0_MATRA
        assert hm.from_name("SLOKA") == Level.L4_SLOKA
        with pytest.raises(KeyError):
            hm.from_name("nonexistent")

    def test_constituent_child_weights(self):
        c = Constituent(
            parent=ProsodicUnit(weight=Trit.S2, level=Level.L2_GANA),
            children=[
                ProsodicUnit(weight=Trit.S1),
                ProsodicUnit(weight=Trit.S1),
            ],
        )
        assert c.child_weights() == [Trit.S1, Trit.S1]

    def test_edge_license_defaults(self):
        e = EdgeLicense()
        assert e.position == "right"
        assert not e.allows_anceps


# ===================================================================
# §3  Trit Algebra
# ===================================================================

class TestTritAlgebra:
    """Tests for Spec Section 3: Trit Algebra."""

    # -- 3.2.1  Addition table --

    def test_s1_plus_s1(self):
        assert trit_add(Trit.S1, Trit.S2) == Trit.S3

    def test_s1_plus_s2(self):
        assert trit_add(Trit.S1, Trit.S1) == Trit.S2

    def test_overflow(self):
        assert trit_add(Trit.S2, Trit.S2) is OVERFLOW
        assert trit_add(Trit.S3, Trit.S1) is OVERFLOW
        assert trit_add(Trit.S3, Trit.S3) is OVERFLOW

    def test_commutativity(self):
        for a in Trit:
            for b in Trit:
                assert trit_add(a, b) == trit_add(b, a)

    def test_add_seq(self):
        assert trit_add_seq([Trit.S1, Trit.S2]) == Trit.S3
        assert trit_add_seq([Trit.S1]) == Trit.S1
        assert trit_add_seq([Trit.S1, Trit.S1]) == Trit.S2

    def test_add_seq_overflow(self):
        # S1 + S2 = S3, then S3 + S2 = overflow
        result = trit_add_seq([Trit.S1, Trit.S2, Trit.S2])
        assert result is OVERFLOW

    def test_add_seq_empty_raises(self):
        with pytest.raises(ValueError):
            trit_add_seq([])

    # -- 3.2.2  Tension pairing --

    def test_tension_pair_valid(self):
        assert tension_pair(Trit.S1, Tension.SURPLUS, Trit.S1, Tension.DEBT)

    def test_tension_pair_invalid_no_cancel(self):
        assert not tension_pair(Trit.S1, Tension.SURPLUS, Trit.S1, Tension.SURPLUS)

    def test_tension_pair_with_budget(self):
        b = Budget(min_weight=Trit.S1, max_weight=Trit.S2)
        assert tension_pair(Trit.S1, Tension.SURPLUS, Trit.S1, Tension.DEBT, b)

    # -- 3.2.3  Projection --

    def test_project_leaf(self):
        u = ProsodicUnit(weight=Trit.S2, level=Level.L0_MATRA)
        assert project(u, Level.L0_MATRA) == 1

    def test_project_constituent(self):
        foot = Constituent(
            parent=ProsodicUnit(weight=Trit.S2, level=Level.L2_GANA),
            children=[
                ProsodicUnit(weight=Trit.S1, level=Level.L0_MATRA),
                ProsodicUnit(weight=Trit.S1, level=Level.L0_MATRA),
            ],
        )
        assert project(foot, Level.L0_MATRA) == 0  # S1 values = 0 each

    # -- 3.2.4  Completion (Prastara) --

    def test_complete_two_positions_budget_s2(self):
        b = Budget(min_weight=Trit.S2, max_weight=Trit.S2, exact=True)
        results = enumerate_patterns(2, b)
        # S1+S1 = 0+0 = 0 ≠ 1, so no match... wait
        # Budget.satisfied checks total = sum of .value
        # S2 exact means total must == 1
        # S1+S1 = 0+0 = 0 ≠ 1
        # S1+S2 = 0+1 = 1 ✓
        # S2+S1 = 1+0 = 1 ✓
        # S2+S2 = 1+1 = 2 ≠ 1
        assert [Trit.S1, Trit.S2] in results
        assert [Trit.S2, Trit.S1] in results
        assert len(results) == 2

    def test_complete_three_positions_budget_s1(self):
        b = Budget(min_weight=Trit.S1, max_weight=Trit.S1, exact=True)
        results = enumerate_patterns(3, b)
        # Total must == 0 (S1 value). All positions S1.
        assert results == [[Trit.S1, Trit.S1, Trit.S1]]

    def test_complete_with_partial(self):
        b = Budget(min_weight=Trit.S2, max_weight=Trit.S2, exact=True)
        partial = [Trit.S1, None]
        results = complete(partial, b)
        assert results == [[Trit.S1, Trit.S2]]


# ===================================================================
# §10.1  Checker
# ===================================================================

class TestChecker:
    """Tests for Spec Section 10.1: Checker Algorithm."""

    def test_valid_foot(self):
        foot = Constituent(
            parent=ProsodicUnit(weight=Trit.S2, level=Level.L2_GANA),
            children=[
                ProsodicUnit(weight=Trit.S1, level=Level.L0_MATRA),
                ProsodicUnit(weight=Trit.S1, level=Level.L0_MATRA),
            ],
        )
        result = check_tree(foot)
        assert result.valid
        assert result.nodes_checked == 3

    def test_conservation_violation(self):
        foot = Constituent(
            parent=ProsodicUnit(weight=Trit.S3, level=Level.L2_GANA),
            children=[
                ProsodicUnit(weight=Trit.S1, level=Level.L0_MATRA),
                ProsodicUnit(weight=Trit.S1, level=Level.L0_MATRA),
            ],
        )
        result = check_tree(foot)
        assert not result.valid
        assert any(e.kind == ErrorKind.CONSERVATION for e in result.errors)

    def test_overflow_detection(self):
        foot = Constituent(
            parent=ProsodicUnit(weight=Trit.S3, level=Level.L2_GANA),
            children=[
                ProsodicUnit(weight=Trit.S2, level=Level.L0_MATRA),
                ProsodicUnit(weight=Trit.S2, level=Level.L0_MATRA),
            ],
        )
        result = check_tree(foot)
        assert not result.valid
        assert any(e.kind == ErrorKind.OVERFLOW for e in result.errors)

    def test_budget_violation(self):
        # Budget says max total weight value = 0 (S1), but children sum to 1
        budget = Budget(min_weight=Trit.S1, max_weight=Trit.S1, exact=True)
        foot = Constituent(
            parent=ProsodicUnit(weight=Trit.S3, level=Level.L2_GANA),
            children=[
                ProsodicUnit(weight=Trit.S1, level=Level.L0_MATRA),
                ProsodicUnit(weight=Trit.S2, level=Level.L0_MATRA),
            ],
            budget=budget,
        )
        result = check_tree(foot)
        assert not result.valid
        assert any(e.kind == ErrorKind.BUDGET for e in result.errors)

    def test_nested_tree(self):
        """Two valid feet inside a valid line."""
        foot1 = Constituent(
            parent=ProsodicUnit(weight=Trit.S2, level=Level.L2_GANA),
            children=[
                ProsodicUnit(weight=Trit.S1),
                ProsodicUnit(weight=Trit.S1),
            ],
        )
        foot2 = Constituent(
            parent=ProsodicUnit(weight=Trit.S1, level=Level.L2_GANA),
            children=[
                ProsodicUnit(weight=Trit.S1),
            ],
        )
        line = Constituent(
            parent=ProsodicUnit(weight=Trit.S3, level=Level.L3_PADA),
            children=[foot1, foot2],
        )
        result = check_tree(line)
        assert result.valid

    def test_empty_constituent(self):
        foot = Constituent(
            parent=ProsodicUnit(weight=Trit.S1, level=Level.L2_GANA),
            children=[],
        )
        result = check_tree(foot)
        assert not result.valid
        assert any(e.kind == ErrorKind.EMPTY_CONSTITUENT for e in result.errors)


# ===================================================================
# §6  TME-6 Encoding
# ===================================================================

class TestTME6:
    """Tests for Spec Section 6: TME-6 Binary Encoding."""

    def test_opcode_range(self):
        for op in Opcode:
            assert 0 <= op.value <= 63

    def test_encode_s1_s2(self):
        units = [
            ProsodicUnit(weight=Trit.S1, tension=Tension.NEUTRAL),
            ProsodicUnit(weight=Trit.S2, tension=Tension.NEUTRAL),
        ]
        opcodes = encode_tme6(units)
        # Should use trit-pair encoding: TP_S1_N (15), TP_S2_N (18)
        ints = opcodes_to_ints(opcodes)
        assert 15 in ints  # TP_S1_N
        assert 18 in ints  # TP_S2_N

    def test_encode_decode_roundtrip(self):
        units = [
            ProsodicUnit(weight=Trit.S1, tension=Tension.NEUTRAL),
            ProsodicUnit(weight=Trit.S2, tension=Tension.DEBT),
            ProsodicUnit(weight=Trit.S3, tension=Tension.SURPLUS),
        ]
        opcodes = encode_tme6(units)
        decoded = decode_tme6(opcodes)
        assert len(decoded) == len(units)
        for orig, dec in zip(units, decoded):
            assert orig.weight == dec.weight
            assert orig.tension == dec.tension


# ===================================================================
# §7  Base64-TME
# ===================================================================

class TestBase64TME:
    """Tests for Spec Section 7: Base64-TME Serialization."""

    def test_spec_example(self):
        """Spec example: PUSH_FRAME SET_LEVEL_2 SET_WEIGHT_S2 SET_WEIGHT_S1 POP_FRAME."""
        result = to_base64tme([11, 8, 1, 0, 12])
        assert result == "B810C"

    def test_roundtrip(self):
        values = [0, 1, 2, 15, 18, 21, 63]
        encoded = to_base64tme(values)
        decoded = from_base64tme(encoded)
        assert decoded == values

    def test_invalid_value(self):
        with pytest.raises(ValueError):
            to_base64tme([64])

    def test_invalid_char(self):
        with pytest.raises(ValueError):
            from_base64tme("B810C!")

    def test_metrical_content_detection(self):
        assert is_metrical_content("FGHI")  # contains trit-pair chars
        assert not is_metrical_content("B810C")  # control only

    def test_annotate(self):
        annotations = annotate_stream("B810C")
        assert annotations[0] == ("B", 11, "PUSH_FRAME")
        assert annotations[4] == ("C", 12, "POP_FRAME")


# ===================================================================
# §8  MSS Surface Syntax
# ===================================================================

class TestMSS:
    """Tests for Spec Section 8: MSS Surface Syntax."""

    def test_parse_weight(self):
        tokens = parse_mss(r"\TME[1:W:2]")
        assert len(tokens) == 1
        assert tokens[0].opcode == "W"
        assert tokens[0].params == ["2"]

    def test_parse_multiple(self):
        text = r"\TME[1:W:0] \TME[1:W:1] \TME[1:W:2]"
        tokens = parse_mss(text)
        assert len(tokens) == 3

    def test_parse_frame(self):
        tokens = parse_mss(r"\TME[1:F:push]")
        assert tokens[0].opcode == "F"
        assert tokens[0].params == ["push"]

    def test_parse_to_units(self):
        text = r"\TME[1:T:-1]\TME[1:W:1]\TME[1:W:0]"
        units = parse_mss_to_units(text)
        assert len(units) == 2
        assert units[0].weight == Trit.S2
        assert units[0].tension == Tension.DEBT
        assert units[1].tension == Tension.NEUTRAL  # reset after use

    def test_emit_roundtrip(self):
        u = ProsodicUnit(weight=Trit.S2, tension=Tension.DEBT, level=Level.L2_GANA)
        mss_str = emit_mss(u)
        units = parse_mss_to_units(mss_str)
        assert len(units) == 1
        assert units[0].weight == Trit.S2
        assert units[0].tension == Tension.DEBT


# ===================================================================
# §4  QuantitativeMetrics Overlay
# ===================================================================

class TestQuantitativeMetrics:
    """Tests for Spec Section 4: QuantitativeMetrics Overlay."""

    def test_classify_open_short(self):
        assert classify_syllable(False, False) == SyllableType.OPEN_SHORT

    def test_classify_closed(self):
        assert classify_syllable(False, True) == SyllableType.CLOSED_OR_LONG

    def test_classify_long_vowel(self):
        assert classify_syllable(True, False) == SyllableType.CLOSED_OR_LONG

    def test_classify_superheavy(self):
        assert classify_syllable(True, True) == SyllableType.SUPERHEAVY

    def test_resolution(self):
        u = ProsodicUnit(weight=Trit.S2, tension=Tension.SURPLUS)
        r1, r2 = resolve_heavy(u)
        assert r1.weight == Trit.S1
        assert r2.weight == Trit.S1
        assert r1.tension == Tension.SURPLUS
        assert r2.tension == Tension.NEUTRAL

    def test_resolution_requires_s2(self):
        u = ProsodicUnit(weight=Trit.S1)
        with pytest.raises(ValueError):
            resolve_heavy(u)

    def test_iambic_metron_null(self):
        metron = QuantitativeMetrics.iambic_metron(SyncopationType.NULL)
        weights = [u.weight for u in metron]
        assert weights == [Trit.S1, Trit.S2, Trit.S1, Trit.S2]

    def test_syllable_builder(self):
        s = QuantitativeMetrics.syllable(vowel_long=True)
        assert s.weight == Trit.S2
        assert s.level == Level.L1_AKSARA


# ===================================================================
# §9  Renderers
# ===================================================================

class TestRenderers:
    """Tests for Spec Section 9: MRP Rendering Protocol."""

    def test_scansion(self):
        units = [
            ProsodicUnit(weight=Trit.S2),
            ProsodicUnit(weight=Trit.S1),
            ProsodicUnit(weight=Trit.S2),
        ]
        result = render_scansion(units)
        assert "–" in result
        assert "u" in result

    def test_token_stream(self):
        units = [
            ProsodicUnit(weight=Trit.S1),
            ProsodicUnit(weight=Trit.S2),
            ProsodicUnit(weight=Trit.S1),
            ProsodicUnit(weight=Trit.S2),
        ]
        tokens = render_token_stream(units, foot_size=2)
        assert any(t.is_boundary for t in tokens)

    def test_stream_validator(self):
        target = [
            MetricalToken(weight=Trit.S1, position=0),
            MetricalToken(weight=Trit.S2, position=1),
        ]
        v = StreamValidator(target=target)
        assert v.accept(Trit.S1)
        assert v.accept(Trit.S2)
        assert v.complete

    def test_stream_validator_reject(self):
        target = [MetricalToken(weight=Trit.S1, position=0)]
        v = StreamValidator(target=target)
        assert not v.accept(Trit.S2)  # wrong weight


# ===================================================================
# CLI helpers
# ===================================================================

class TestCLI:
    """Tests for CLI pattern parsing."""

    def test_parse_classical(self):
        trits = parse_pattern("-u-u")
        assert trits == [Trit.S2, Trit.S1, Trit.S2, Trit.S1]

    def test_parse_digit(self):
        trits = parse_pattern("0102")
        assert trits == [Trit.S1, Trit.S2, Trit.S1, Trit.S3]

    def test_parse_with_separators(self):
        trits = parse_pattern("- u | - u")
        assert trits == [Trit.S2, Trit.S1, Trit.S2, Trit.S1]

    def test_trits_to_str_classical(self):
        result = trits_to_str([Trit.S2, Trit.S1, Trit.S2], "classical")
        assert "–" in result
        assert "u" in result

    def test_invalid_char(self):
        with pytest.raises(ValueError):
            parse_pattern("xyz")


class TestCLIUmbrellaCommands:
    """Tests for workflow-oriented CLI commands."""

    def test_cmd_doctor_success(self, monkeypatch, capsys):
        monkeypatch.setattr(mcore_cli.sys, "version_info", (3, 12, 0))
        monkeypatch.setattr(mcore_cli, "_check_module_import", lambda _name: (True, None))

        result = mcore_cli.cmd_doctor(argparse.Namespace())

        output = capsys.readouterr().out
        assert result == 0
        assert "DOCTOR OK" in output

    def test_cmd_doctor_failure(self, monkeypatch, capsys):
        monkeypatch.setattr(mcore_cli.sys, "version_info", (3, 10, 0))

        def fake_import_check(name: str):
            if name == "pytest":
                return False, "missing"
            return True, None

        monkeypatch.setattr(mcore_cli, "_check_module_import", fake_import_check)

        result = mcore_cli.cmd_doctor(argparse.Namespace())

        output = capsys.readouterr().out
        assert result == 1
        assert "DOCTOR FAILED" in output

    def test_cmd_smoke_success(self, capsys):
        result = mcore_cli.cmd_smoke(argparse.Namespace())

        output = capsys.readouterr().out
        assert result == 0
        assert "SMOKE OK" in output

    def test_cmd_notebook_smoke_missing_file(self, tmp_path, capsys):
        notebook_path = tmp_path / "does-not-exist.ipynb"
        args = argparse.Namespace(notebook=str(notebook_path), timeout=5)

        result = mcore_cli.cmd_notebook_smoke(args)

        output = capsys.readouterr().out
        assert result == 1
        assert "not found" in output

    def test_cmd_notebook_smoke_success(self, monkeypatch, tmp_path, capsys):
        notebook_path = tmp_path / "demo.ipynb"
        notebook_path.write_text("{}", encoding="utf-8")
        args = argparse.Namespace(notebook=str(notebook_path), timeout=10)

        observed = {}

        def fake_run(cmd, capture_output, text):
            observed["cmd"] = cmd
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="ok", stderr="")

        monkeypatch.setattr(mcore_cli.subprocess, "run", fake_run)

        result = mcore_cli.cmd_notebook_smoke(args)

        output = capsys.readouterr().out
        assert result == 0
        assert "NOTEBOOK SMOKE OK" in output
        assert observed["cmd"][0] == mcore_cli.sys.executable
        assert "--execute" in observed["cmd"]
        assert str(notebook_path) in observed["cmd"]
