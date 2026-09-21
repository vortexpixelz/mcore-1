# MINT-GLACIER-847291 — counterfeit receipt

Calibration target: a valid locally checkable resolution proof with one forged justification edge.

The forge changes one parent reference while preserving the derived clause and every downstream proof line.
The ordinary verifier therefore has a precise first bad inference.

## V1 — scalar proof-line adapter

Each proof line is compressed to one trit checksum and fed through the frozen MCORE tree.
Runs 227 and 228 reproduced the same negative result: the checksum changes exactly at the forged step,
but the checker produces no new conservation/overflow error. That miss is preserved as an explicit test.

## V2 — topology-native local provenance adapter

Each inference becomes an ordered two-child MCORE constituent. Children encode graph-theoretic provenance
edge span; the parent weight is frozen from the intact proof. The forged edge changes a local span while
the conclusion and downstream syntax remain unchanged.

The V2 test requires the intact control to stay clean and the forged proof to produce exactly one local
MCORE error at the first forged inference.

This edge-span encoding is deliberately minimal and calibration-specific. It is not yet a general proof-DAG
representation; graph unfolding, shared-premise topology, and richer edge features remain open.

Claim boundary: certificate-auditing benchmark only. This experiment says nothing about whether P equals NP.

Run: pytest -q tests/test_proof_probe.py

## V3 — strong counterfeit scenario

V3 strengthens the benchmark scenario; it reuses the unchanged V2 edge-span adapter.
The default certificate has 24 inferences. Exactly the left justification edge at
step 3 (id 28) is changed from id 27 to id 26. All conclusions, pivots, ids, right
edges, and the entire downstream suffix remain unchanged. The 21 later steps
continue the dependency chain through the final empty clause.

`terminal_proof_verdict` checks every inference, accumulating failure while
continuing with the declared clauses. Its only output is a boolean after the
whole certificate. It accepts the intact control and rejects the forgery without
returning a location. Merely checking the last empty clause would incorrectly
accept both certificates; that is not the comparator used here.

MCORE receives the intact frozen topology and observed syntax, never the verifier
verdict or ground-truth location. It reports one CONSERVATION error at step 3 and
no intact-control errors. Tests independently establish that only step 3 is
locally invalid and that all 21 downstream steps are processed. The receipt keeps
ground truth separate from the boolean-only terminal result.

This is a reporting/localization comparison, not evidence that MCORE detects
invalidity faster than a local verifier. The ordinary local verifier can also
identify step 3. The adapter needs the intact reference and detects this chosen
edge-span mutation; it is not a general proof verifier, a Hodge/cochain V3
architecture, or a demonstration on an LRAT corpus. No P vs NP inference follows.

Reproduce the deterministic receipt (canonical JSON artifacts and SHA-256 hashes):

```sh
PYTHONPATH=src python -m mcore_1.proof_probe > experiments/counterfeit_receipt/receipts/strong-v3.json
PYTHONHASHSEED=42 PYTHONPATH=src pytest -q
```

The frozen run-230 V1/V2 receipt remains unchanged. JHTDB/NS-001 is outside scope.

Local validation of this extension: 306 passed, 3 skipped; fatal-error lint passed.
Environment: Python 3.12.3, pytest 9.1.1, NumPy 2.5.3, SciPy 1.18.1,
PyYAML 6.0.3. This local environment is separate from the pinned CI environment;
these results do not claim a Docker or CI run. All seven proof-probe tests passed.
