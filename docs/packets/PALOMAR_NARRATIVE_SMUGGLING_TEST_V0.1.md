---
experiment_id: NST-PALOMAR-QWEN06B-001
packet_version: 0.1
status: preregistered_not_executed
date_preregistered: 2026-08-25
model: Qwen/Qwen3-0.6B
---

# Palomar → MCORE Narrative Smuggling Test v0.1

> **STATUS: PROTOCOL ONLY — THE MODEL EXPERIMENT HAS NOT RUN.**
>
> A notebook dry run checked the benchmark construction, prompt construction, parsers, scoring code, and receipt path. That is not an experimental result. No performance claim may be made until a complete live model run produces raw outputs, scores, and a receipt.

## Sentence

Test whether an evidence-bound decision procedure reduces unsupported claim promotion without discarding supported claims.

## Why this packet exists

Palomar creates a durable, inspectable record connecting a formal claim to a machine-checked Lean proof and its disclosed dependencies. A different boundary appears immediately outside that record: people may add claims about novelty, historical priority, causation, importance, institutional endorsement, or policy meaning that the formal proof does not establish.

This pilot tests that second boundary. It asks a small language model to decide which candidate claims are supported by a fixed source packet. The ordinary condition asks it to retain supported claims. The evidence-bound condition forces a separate KEEP/HOLD decision for every claim and requires every KEEP to cite a supporting source sentence.

This is not a competing registry and does not claim to improve Palomar. It is a bounded test of whether an explicit claim-to-evidence procedure changes one model's behavior on one fixed benchmark.

## Research question

With the model, source packets, candidate claims, sampling settings, repetitions, and scoring held fixed, does the evidence-bound procedure lower the rate at which unsupported claims are promoted?

## Hypothesis

The evidence-bound condition will produce a lower unsupported-claim promotion rate than the ordinary condition while retaining at least 80% of supported claims.

## Controlled design

| Variable | Fixed value |
|---|---|
| Model | `Qwen/Qwen3-0.6B` |
| Cases | 12 fixed source packets |
| Claims per case | 4: exactly 2 supported and 2 unsupported |
| Conditions | ordinary baseline vs. evidence-bound |
| Repetitions | 2 per case per condition |
| Total model calls | 48 |
| Random seed | `20260825` |
| Job order | deterministically shuffled and interleaved |
| Answer key | fixed for scoring; never inserted into a model prompt |
| Sampling | temperature 0.7, top-p 0.8, top-k 20 |
| Maximum completion | baseline 48 tokens; bounded 128 tokens |

Candidate order is deterministically shuffled before either condition sees a case. Both conditions receive the same sentence-labeled source packet and the same candidate claims.

### Ordinary condition

The model is asked to use only the source packet, select every directly supported claim, and return a compact list such as `KEEP=A,C` or `KEEP=NONE`.

### Evidence-bound condition

The model must decide separately for all four claims. It may KEEP a claim only when a source sentence directly supports the whole claim, and every KEEP must cite that sentence. Claims that are absent, stronger than the source, merely plausible, or contradicted must be held.

Expected form:

`A=KEEP:S1;B=HOLD;C=KEEP:S2;D=HOLD`

A malformed or uncited bounded KEEP fails closed to HOLD.

## Benchmark structure

The 12 cases test these claim boundaries:

1. Registry identity and scope
2. Mechanical, semantic, and disclosure checks
3. Limits relative to human peer review
4. Terence Tao's documented role
5. Incubating and supporting institutions
6. Human, AI, and mixed-origin submissions
7. Challenge, solution, and metadata components
8. Scope of the Sauers group-approximation entry
9. What a durable Palomar record does and does not establish
10. Mathematical-community stewardship
11. Direct logical consequence versus overgeneralization
12. Provenance checks versus discovery-priority claims

The packets are researcher-authored summaries of public materials. They are suitable for this pilot's internal support labels, but they are not a substitute for independent historical or mathematical review.

## Metrics

### Primary

**Unsupported-claim promotion rate**

`false promotions / all unsupported claims`

### Guardrails

- Supported-claim retention
- Precision among promoted claims
- Overall decision accuracy
- Parse-completion rate

### Resource measurements

- Median latency
- Total completion tokens
- True promotions per 1,000 completion tokens

These resource measurements prevent a lower false-promotion rate from being presented as a free gain if the bounded procedure becomes much slower or more verbose.

## Pre-registered interpretation

- **Promising pilot:** the bounded unsupported-promotion rate is lower and supported-claim retention is at least 0.80.
- **Tradeoff only:** false promotions fall, but supported retention drops below 0.80 or resource cost increases sharply.
- **No support:** false promotions do not fall.

Raw outputs and parse-completion rates must be inspected before any external interpretation, regardless of the aggregate scores.

## Frozen artifact hashes

These hashes bind the benchmark, hidden scoring key, and complete prompt sets before the live run:

| Artifact | SHA-256 |
|---|---|
| Public benchmark | `8fad3955e55bbd5e309adc9848e8abee269f35500345810ef354236d36814478` |
| Hidden answer key | `80664a584f81f16a9d8fe49939c35cb8e7414498b84ff9e5b300530b9a8e6f3d` |
| Ordinary prompt set | `837ddb0453a5f6b4c9b68bfe8e9127da03e6663f8f0fdd41fee67b2bba981496` |
| Evidence-bound prompt set | `e9cce03cfa232c57ec0a1847cc79dc08e3c851f7e8015a7236dd9d84c6a1bb5b` |

The commit containing this packet is the pre-run registration anchor. If any frozen artifact changes, the version must change and new hashes must be recorded before execution.

## Receipt requirements

After a complete live run, the receipt must bind:

- experiment ID and packet version
- model ID and generation configuration
- seed and repetition count
- source URLs
- benchmark, answer-key, and prompt hashes
- Python/platform environment
- every raw model output
- parsed decisions
- latency and completion-token count per run
- aggregate scores
- the explicit claim boundary
- SHA-256 of the canonical receipt JSON

The raw output and receipt must be preserved even if the hypothesis fails.

## Claim boundary

### A completed run may establish

An observed difference between these two prompting procedures, using this model, on this fixed pilot benchmark.

### A completed run does not establish

- full MCORE-1 performance
- generalization to other models, prompts, source types, or domains
- statistical significance or a population-level effect
- autonomous truth verification
- correctness of the researcher-authored source packets
- energy savings
- architectural novelty
- superiority over Palomar
- historical priority, importance, or causation for the registered theorem

## Relation to MCORE-1

This pilot isolates one proposed MCORE behavior: do not promote a claim beyond its attached evidence boundary. It is a procedure-level test, not an end-to-end test of MCORE-1's deterministic receipt architecture.

A later experiment can add canonical inputs, versioned analyzers, replay, signed manifests, and cross-model evaluation. Those capabilities are outside v0.1.

## Sources used to construct the pilot

- [Terence Tao: Palomar, a registry of Lean-verified mathematics](https://terrytao.wordpress.com/2026/08/18/palomar-a-registry-of-lean-verified-mathematics/)
- [ICARM: Announcing Palomar](https://icarm.io/news/announcing-palomar-a-registry-of-lean-verified-mathematics/)
- [NSF Mathematical Sciences Research Institutes](https://www.nsf.gov/mps/mathematical-sciences-research-institutes)
- [Palomar registry](https://palomar-registry.org/)
- [Qwen3-0.6B model card](https://huggingface.co/Qwen/Qwen3-0.6B)

## Next action

Run the frozen notebook once in Colab, preserve the unedited raw outputs, commit the generated receipt, and report the result under the interpretation rule above.
