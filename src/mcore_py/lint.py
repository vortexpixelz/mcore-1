"""
MCORE-1 Lint Engine (feat/mcore-lint-engine)
=============================================

Scores arbitrary text against the MCORE-1 metrical conservation rules and
returns a continuous risk score R ∈ [0, 1].  A two-threshold policy maps
that score to an action decision:

    R <= T_low             → "no"   (output is fine, send immediately)
    T_low < R < T_high     → "maybe" (cheap self-correction turn)
    R >= T_high            → "yes"  (full revision turn required)

This module integrates directly with the existing MCORE-1 API:
  - mss.parse_mss_to_units()  : text → ProsodicUnit list
  - checker.check_tree()      : Constituent → CheckResult
  - algebra.trit_add_seq()    : weight pooling
  - model.*                   : Trit, Level, Constituent, ProsodicUnit

No new dependencies beyond what is already in requirements.txt.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Literal

from mcore_py.algebra import trit_add_seq, OVERFLOW
from mcore_py.checker import check_tree, ErrorKind
from mcore_py.model import Budget, Constituent, Level, ProsodicUnit, Trit
from mcore_py.mss import parse_mss_to_units


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class LintConfig:
    """Threshold and weight configuration for the MCORE-1 lint engine.

    Parameters
    ----------
    T_low : float
        Risk scores at or below this value → action "no" (send immediately).
    T_high : float
        Risk scores at or above this value → action "yes" (full revision).
        Scores between T_low and T_high → action "maybe" (cheap fix).
    weight_overflow : float
        Contribution weight for OVERFLOW errors (most severe).
    weight_conservation : float
        Contribution weight for CONSERVATION errors.
    weight_budget : float
        Contribution weight for BUDGET errors.
    weight_other : float
        Contribution weight for all other error kinds.
    mode : str
        "always" — lint every call.
        "tagged" — only lint when the prompt contains the tag string.
    tag : str
        The tag string to look for when mode="tagged".
    max_errors_norm : int
        Number of errors that would produce R = 1.0  (normalization ceiling).
    """
    T_low: float = 0.25
    T_high: float = 0.65
    weight_overflow: float = 1.0
    weight_conservation: float = 0.6
    weight_budget: float = 0.4
    weight_other: float = 0.2
    mode: str = "always"
    tag: str = "[MCORE-LINT]"
    max_errors_norm: int = 10

    @classmethod
    def from_dict(cls, d: dict) -> "LintConfig":
        """Build a LintConfig from a plain dict (e.g. loaded from YAML)."""
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


# Default config — can be overridden at call site or loaded from YAML
DEFAULT_CONFIG = LintConfig()


# ---------------------------------------------------------------------------
# Text → Constituent helper
# ---------------------------------------------------------------------------

def _text_to_constituent(text: str) -> Constituent | None:
    """Convert raw text to a flat Constituent using the MSS parser.

    Returns None if the text produces no ProsodicUnits (e.g. empty string).
    """
    try:
        units: list[ProsodicUnit] = parse_mss_to_units(text)
    except Exception:
        # If the MSS parser rejects the input entirely, treat as zero units
        units = []

    if not units:
        return None

    pooled = trit_add_seq([u.weight for u in units])
    if pooled is OVERFLOW:
        # Overflow at the top level — represent as max weight
        parent_weight = Trit.S3
    else:
        parent_weight = pooled  # type: ignore[assignment]

    parent = ProsodicUnit(weight=parent_weight, level=Level.L3_PADA)
    return Constituent(parent=parent, children=units)


# ---------------------------------------------------------------------------
# Core scoring
# ---------------------------------------------------------------------------

def lint_score(text: str, cfg: LintConfig | None = None) -> float:
    """Compute a risk score R ∈ [0, 1] for *text* using MCORE-1 rules.

    A score of 0.0 means fully well-formed (no violations); 1.0 means
    maximally ill-formed.  The score is derived from the weighted count of
    CheckErrors produced by check_tree(), normalized to [0, 1].

    Parameters
    ----------
    text : str
        The raw text to score (e.g. a tweet draft, a model response).
    cfg : LintConfig | None
        Configuration.  Defaults to DEFAULT_CONFIG if None.

    Returns
    -------
    float
        Risk score R ∈ [0, 1].

    Examples
    --------
    >>> score = lint_score("Hello world")
    >>> 0.0 <= score <= 1.0
    True
    """
    if cfg is None:
        cfg = DEFAULT_CONFIG

    constituent = _text_to_constituent(text)

    # Empty / unparseable input — treat as neutral (score 0.5)
    if constituent is None:
        return 0.5

    result = check_tree(constituent)

    if result.valid:
        return 0.0

    # Weighted error accumulation
    _kind_weight = {
        ErrorKind.OVERFLOW:            cfg.weight_overflow,
        ErrorKind.CONSERVATION:        cfg.weight_conservation,
        ErrorKind.BUDGET:              cfg.weight_budget,
        ErrorKind.TENSION_UNRESOLVED:  cfg.weight_other,
        ErrorKind.EMPTY_CONSTITUENT:   cfg.weight_other,
    }

    raw = sum(_kind_weight.get(err.kind, cfg.weight_other) for err in result.errors)

    # Normalize: raw / (max_errors_norm * max_single_weight)
    ceiling = cfg.max_errors_norm * cfg.weight_overflow
    R = raw / ceiling if ceiling > 0 else 1.0

    return max(0.0, min(1.0, R))  # clamp to [0, 1]


# ---------------------------------------------------------------------------
# Decision gate
# ---------------------------------------------------------------------------

Action = Literal["no", "maybe", "yes"]


def decide(score: float, cfg: LintConfig | None = None) -> Action:
    """Map a risk score to an action decision.

    Parameters
    ----------
    score : float
        Risk score from lint_score(), in [0, 1].
    cfg : LintConfig | None
        Configuration with T_low and T_high thresholds.

    Returns
    -------
    Action
        "no"    — score <= T_low  : send output immediately.
        "maybe" — T_low < score < T_high : run a cheap correction turn.
        "yes"   — score >= T_high : run a full revision turn.

    Examples
    --------
    >>> cfg = LintConfig(T_low=0.25, T_high=0.65)
    >>> decide(0.1, cfg)
    'no'
    >>> decide(0.4, cfg)
    'maybe'
    >>> decide(0.9, cfg)
    'yes'
    """
    if cfg is None:
        cfg = DEFAULT_CONFIG

    if score <= cfg.T_low:
        return "no"
    elif score >= cfg.T_high:
        return "yes"
    else:
        return "maybe"


# ---------------------------------------------------------------------------
# Tweet engine
# ---------------------------------------------------------------------------

@dataclass
class TweetEngineResult:
    """Result from tweet_engine().

    Attributes
    ----------
    text : str
        Final output text (possibly revised).
    action : Action
        The decision that was made: "no", "maybe", or "yes".
    score : float
        Risk score of the *original* first-turn output.
    turns : int
        Total LLM turns used (1 = no revision, 2 = one revision).
    """
    text: str
    action: Action
    score: float
    turns: int


def tweet_engine(
    prompt: str,
    llm_fn: Callable[[str], str],
    cfg: LintConfig | None = None,
    *,
    maybe_prefix: str = "Revise the following tweet conservatively (stay ≤280 chars):\n",
    yes_prefix: str = "The previous tweet failed MCORE-1 checks. Rewrite it fully from this prompt:\n",
) -> TweetEngineResult:
    """Generate a tweet, score it, and optionally revise it.

    Workflow
    --------
    1. Call llm_fn(prompt) → first draft.
    2. Score the draft with lint_score().
    3. Based on decide():
       - "no"    → return draft as-is  (1 LLM turn).
       - "maybe" → call llm_fn with a light correction prompt  (2 turns).
       - "yes"   → call llm_fn with a full rewrite prompt  (2 turns).

    Parameters
    ----------
    prompt : str
        The generation prompt (topic, tone, constraints, etc.).
    llm_fn : Callable[[str], str]
        Any callable that takes a string prompt and returns a string response.
        Works with OpenAI, Anthropic, local models, or a mock for testing.
    cfg : LintConfig | None
        Configuration.  Defaults to DEFAULT_CONFIG.
    maybe_prefix : str
        Prefix added to the draft for "maybe" revision prompts.
    yes_prefix : str
        Prefix added to the original prompt for "yes" full-rewrite prompts.

    Returns
    -------
    TweetEngineResult
        Contains the final text, the action taken, the original risk score,
        and the number of LLM turns used.

    Examples
    --------
    >>> def mock_llm(p): return "Hello from MCORE!"
    >>> result = tweet_engine("Write a tweet about MCORE-1.", mock_llm)
    >>> result.action in ("no", "maybe", "yes")
    True
    """
    if cfg is None:
        cfg = DEFAULT_CONFIG

    # Respect mode="tagged": skip linting if tag is absent
    skip_lint = cfg.mode == "tagged" and cfg.tag not in prompt

    # Turn 1 — initial generation
    draft = llm_fn(prompt)
    turns = 1

    if skip_lint:
        return TweetEngineResult(text=draft, action="no", score=0.0, turns=turns)

    score = lint_score(draft, cfg)
    action = decide(score, cfg)

    if action == "no":
        return TweetEngineResult(text=draft, action=action, score=score, turns=turns)

    # Turn 2 — revision
    if action == "maybe":
        revision_prompt = maybe_prefix + draft
    else:  # "yes"
        revision_prompt = yes_prefix + prompt

    revised = llm_fn(revision_prompt)
    turns = 2

    return TweetEngineResult(text=revised, action=action, score=score, turns=turns)
