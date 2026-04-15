"""
Tradition Stub Overlays (Spec Section 5)
==========================================

Stubs for Arabic 'arud, Chinese regulated verse (jintishi), and Japanese
mora-timed prosody. These define the hierarchy mappings and trit
interpretations but do not implement full constraint checking.
"""

from __future__ import annotations

from mcore_py.model import HierarchyMap, Level, Trit


# ---------------------------------------------------------------------------
# 5.1  Arabic 'Arud (stub)
# ---------------------------------------------------------------------------

class ArabicArud:
    """Stub overlay for Arabic 'arud system.

    Hierarchy:
        L0: harf (letter)
        L1: sabab/watid/fasila
        L2: taf'ila (metrical foot)
        L3: shatr (hemistich)
        L4: bayt (verse)

    Status: Stub. Full specification requires mapping zihaf rules
    to the trit algebra.
    """

    hierarchy = HierarchyMap({
        Level.L0_MATRA:  ("harf", "letter"),
        Level.L1_AKSARA: ("sabab", "unit"),
        Level.L2_GANA:   ("tafila", "foot"),
        Level.L3_PADA:   ("shatr", "hemistich"),
        Level.L4_SLOKA:  ("bayt", "verse"),
    })

    # Al-Khalil's 16 meters (names only — patterns TBD)
    METERS: list[str] = [
        "tawil", "basit", "wafir", "kamil", "hazaj", "rajaz",
        "ramal", "sarih", "munsarih", "muqtadab", "mujtath",
        "mutaqarib", "mutadarik", "khafif", "madid", "gharib",
    ]

    @staticmethod
    def trit_interpretation() -> dict[Trit, str]:
        return {
            Trit.S1: "short syllable (harakah)",
            Trit.S2: "long syllable (sukun)",
            Trit.S3: "reserved (overlong / madd)",
        }


# ---------------------------------------------------------------------------
# 5.2  Chinese Regulated Verse / jintishi (stub)
# ---------------------------------------------------------------------------

class ChineseJintishi:
    """Stub overlay for Chinese regulated verse.

    Uses tonal rather than weight-based prosodic distinctions:
        S1 = ping (level tone)
        S2 = ze (oblique tone)
        S3 = reserved

    The + operator does not apply for tonal meter; instead,
    pattern-matching constraints use the completion operator.

    Status: Stub. Requires formal treatment of dui (antithesis) constraints.
    """

    hierarchy = HierarchyMap({
        Level.L0_MATRA:  ("zi", "character"),
        Level.L1_AKSARA: ("dou", "phrase"),
        Level.L2_GANA:   ("ju", "line"),
        Level.L3_PADA:   ("lian", "couplet"),
        Level.L4_SLOKA:  ("shi", "poem"),
    })

    @staticmethod
    def trit_interpretation() -> dict[Trit, str]:
        return {
            Trit.S1: "ping (level tone)",
            Trit.S2: "ze (oblique tone)",
            Trit.S3: "reserved",
        }


# ---------------------------------------------------------------------------
# 5.3  Japanese Mora-Timed Prosody (stub)
# ---------------------------------------------------------------------------

class JapaneseMora:
    """Stub overlay for Japanese mora-timed prosody.

    Japanese verse is mora-counted, making it the closest to MCORE-1's
    default weight model:
        S1 = 1 mora (short syllable: ka, ta, na)
        S2 = 2 morae (long vowel, geminate, nasal coda: kaa, kka, kan)
        S3 = 3 morae (rare: long vowel + nasal)

    Budget constraints encode haiku (5-7-5), tanka (5-7-5-7-7), etc.
    The ji-amari (excess character) phenomenon maps to budget tolerance.

    Status: Stub. Requires formal treatment of kireji (cutting word) boundaries.
    """

    hierarchy = HierarchyMap({
        Level.L0_MATRA:  ("on", "mora"),
        Level.L1_AKSARA: ("ji", "character"),
        Level.L2_GANA:   ("ku", "line/phrase"),
        Level.L3_PADA:   ("renku", "stanza"),
        Level.L4_SLOKA:  ("uta", "poem"),
    })

    # Standard form budgets (total morae per line)
    HAIKU = [5, 7, 5]
    TANKA = [5, 7, 5, 7, 7]
    SEDOKA = [5, 7, 7, 5, 7, 7]

    @staticmethod
    def trit_interpretation() -> dict[Trit, str]:
        return {
            Trit.S1: "1 mora (short syllable)",
            Trit.S2: "2 morae (long vowel / geminate / nasal coda)",
            Trit.S3: "3 morae (long vowel + nasal, rare)",
        }
