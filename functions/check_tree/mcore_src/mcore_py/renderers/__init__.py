"""
MRP Rendering Protocol (Spec Section 9)
=========================================

Defines how MCORE-1 data is rendered for specific output media:
  - Terminal: ANSI color/formatting
  - Audio: beat/pitch mapping (requires external audio lib)
  - TokenStream: inline attributes for LLM constrained decoding
"""

from mcore_py.renderers.terminal import render_terminal
from mcore_py.renderers.token_stream import render_token_stream

__all__ = ["render_terminal", "render_token_stream"]
