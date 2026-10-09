# Recursive S2.5 → S3 scope check

This is a pinned, reviewable candidate-graph result for the placement of the S3
provider handoff under one of the two S2.5 child regions.

The source says the S3 handoff is within the Pair-1 B1→C1 boundary. The graph
retains both Pair-1 and Pair-2 placements. Three usable model observations
selected/support Pair 1; Laya's first prompt was truncated and is retained as a
failed attempt, while its shorter retry selected Pair 1. Model agreement is
recorded as evidence, not as semantic proof.

The originating local run checked the complete source hashes and exact anchor
character/byte slices. The public packet omits full source files because they
contain workstation paths and local operational details. Its standard-library
verifier checks the retained source digests, anchor offsets and text lengths,
both graph placement relations, their endpoints, and the persisted registry
finding. It does not recompute full-source hashes or run Goggles/SemAlg.

```sh
python3 verify_scope_check.py
```

Result: source and graph checks pass; `CandidateScopePlacement` is not in the
registered constitution catalog used by the originating check. Native semantic
admission, S3 live execution, and semantic compression were not run.

Files:

- `lowered.json`: complete lowered candidate graph and provenance
- `graph-snapshot.json`: SHG-mu structural snapshot
- `model-observations.json`: Laya/Jev/Qwen observations and retry history
- `symbolic-scope-check.json`: symbolic check receipt and limitations
- `metrics.json`: graph and model token figures
- `source-anchors.json`: source digests and exact anchored excerpts/offsets;
  full inputs remain local
- `overview.svg`: compact scope-candidate graph
