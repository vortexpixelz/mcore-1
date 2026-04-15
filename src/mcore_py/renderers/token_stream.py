"""
TokenStream Renderer (Spec Section 9 — MRP)
=============================================

Enables constrained decoding in language models: the model generates text
tokens interleaved with metrical tokens, and a constraint checker validates
consistency with the target meter.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from mcore_py.model import Budget, Level, ProsodicUnit, Tension, Trit


# ---------------------------------------------------------------------------
# Token types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MetricalToken:
    """An inline metrical attribute token for LLM token streams.

    Attributes
    ----------
    weight : Trit
        Expected weight at this position.
    tension : Tension
        Expected tension state.
    level : Level
        Hierarchy level.
    position : int
        Position index in the metrical pattern.
    is_boundary : bool
        True if this is a foot/line boundary marker.
    """
    weight: Trit
    tension: Tension = Tension.NEUTRAL
    level: Level = Level.L1_AKSARA
    position: int = 0
    is_boundary: bool = False

    def to_dict(self) -> dict:
        """Serialize to a dictionary for JSON embedding."""
        return {
            "type": "metrical",
            "weight": self.weight.value,
            "tension": self.tension.value,
            "level": self.level.value,
            "position": self.position,
            "boundary": self.is_boundary,
        }

    def __repr__(self) -> str:
        w = self.weight.name
        t = {Tension.DEBT: "-", Tension.NEUTRAL: "0", Tension.SURPLUS: "+"}[self.tension]
        return f"MT({w},{t},pos={self.position})"


# ---------------------------------------------------------------------------
# TokenStream renderer
# ---------------------------------------------------------------------------

def render_token_stream(
    units: list[ProsodicUnit],
    foot_size: int = 2,
) -> list[MetricalToken]:
    """Convert a sequence of ProsodicUnits to a MetricalToken stream.

    Inserts boundary tokens at foot boundaries.

    Parameters
    ----------
    units : list[ProsodicUnit]
        The metrical pattern.
    foot_size : int
        Number of syllables per foot (for boundary insertion).

    Returns
    -------
    list[MetricalToken]
        Token stream suitable for LLM constrained decoding.
    """
    tokens: list[MetricalToken] = []

    for i, unit in enumerate(units):
        # Insert boundary before foot starts (except at position 0)
        if i > 0 and i % foot_size == 0:
            tokens.append(MetricalToken(
                weight=Trit.S1,  # placeholder
                level=Level.L2_GANA,
                position=i,
                is_boundary=True,
            ))

        tokens.append(MetricalToken(
            weight=unit.weight,
            tension=unit.tension,
            level=unit.level,
            position=i,
        ))

    return tokens


# ---------------------------------------------------------------------------
# Constraint checker for token streams
# ---------------------------------------------------------------------------

@dataclass
class StreamValidator:
    """Validates a text+metrical token stream against a target pattern.

    Usage:
        validator = StreamValidator(target_pattern)
        for text_token in generated_tokens:
            syllable_weight = analyze_syllable(text_token)
            if not validator.accept(syllable_weight):
                reject_token(text_token)
    """
    target: list[MetricalToken]
    position: int = 0
    errors: list[str] = field(default_factory=list)

    def accept(self, weight: Trit, tension: Tension = Tension.NEUTRAL) -> bool:
        """Check whether the next syllable matches the target pattern.

        Parameters
        ----------
        weight : Trit
            Weight of the generated syllable.
        tension : Tension
            Tension state.

        Returns
        -------
        bool
            True if the syllable is valid at the current position.
        """
        if self.position >= len(self.target):
            self.errors.append(f"Exceeded pattern length at position {self.position}")
            return False

        target_tok = self.target[self.position]

        # Skip boundary tokens
        while target_tok.is_boundary and self.position < len(self.target) - 1:
            self.position += 1
            target_tok = self.target[self.position]

        if weight != target_tok.weight:
            self.errors.append(
                f"Position {self.position}: expected {target_tok.weight.name}, "
                f"got {weight.name}"
            )
            return False

        self.position += 1
        return True

    @property
    def complete(self) -> bool:
        """Check whether the entire pattern has been consumed."""
        return self.position >= len(self.target)

    def remaining(self) -> list[MetricalToken]:
        """Return the remaining expected tokens."""
        return self.target[self.position:]
