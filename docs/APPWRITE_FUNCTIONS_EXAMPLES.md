# Example Appwrite Functions (Python 3.12)

Each function uses the same **bundle** layout as `functions/check_tree` (vendor `mcore_src/mcore_py`, `mcore_src/mcore_1`). Copy `functions/check_tree/README.md` packaging steps.

## 1. `trit_algebra` (suggested `$id`: `mcore_trit_algebra`)

**Ops:**

- `{"op": "trit_sum", "trits": [0,1,2]}` → pooled weight name / overflow
- `{"op": "complete", "positions": 3, "budget": 2}` → JSON list of patterns

**Handler sketch:**

```python
def main(context):
    _ensure_mcore_on_path()
    from mcore_py.algebra import OVERFLOW, enumerate_patterns, trit_add_seq
    from mcore_py.model import Budget, Level, Trit
    data = context.req.body_json or {}
    ...
```

## 2. `validate_metrical_pattern`

**Op:** `{"op": "validate", "pattern": "-u-"}`

Reuse `mcore_py.cli.parse_pattern`, build `Constituent` foot as in `mcore_mcp.server.mcore_validate_metrical_pattern`.

## 3. `complete_pattern`

Same as §1 `complete` op — thin wrapper over `enumerate_patterns`.

## 4. `check_tree` (implemented)

See `functions/check_tree/src/main.py` — **reference implementation** for DNA + weight + deletion ops, optional PostHog, and `mcore_1` imports.

## Rust rewrite (optional)

The hot path is `mcore_py.checker` over `Constituent` trees. A Rust port would reimplement that visitor; until then, **Python 3.12 + warm executions** is the pragmatic high-performance option on Appwrite.
