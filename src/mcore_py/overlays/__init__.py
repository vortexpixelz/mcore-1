"""
Tradition-Specific Overlays
============================

Overlays extend MCORE-1 for specific prosodic traditions.

Complete:
  - QuantitativeMetrics: Indo-European quantitative meters

Stubs:
  - ArabicArud: Arabic 'arud system
  - ChineseJintishi: Chinese regulated verse
  - JapaneseMora: Japanese mora-timed prosody
"""

from mcore_py.overlays.quantitative_metrics import QuantitativeMetrics

__all__ = ["QuantitativeMetrics"]
