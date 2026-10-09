# Semantic construction probes

Offline experimental runners and retained model evidence for the co-grown SHG tower. These probes do not implement or admit grammatical construction laws. No Looper route, graph owner, service or model weights are changed.

## Latest results

- [Expanded graph search](expanded-runs/1791507722473455628/report.md): 10 requests, 8 completed candidates, 2 timeouts; no network operands.
- [Immutable lexical substrate](local-runs/1791508633033236665/report.md): preservation passes, explicit construction remains absent.
- [Typed interface probe](typed-local-runs/1791509391213194054/report.md): 5 requests, 3 completed invalid candidates, 2 timeouts. Zero applications/networks. Native adapter and composition were not run.

Each run includes exact requests, outputs or stream journals, diagnostics, source provenance, a standalone `network.html` and a hash manifest. Historical local paths in evidence are provenance, not portable entrypoints. Several historical reports predate later diagnostic checks; their results are not semantic proof.

## Run

Python standard library only:

```bash
cd semantic-construction-probes
python3 check_contracts.py
python3 typed_local.py
```

Qwen uses the existing OpenAI-compatible server at `127.0.0.1:8088`; Laya diagnostic runners use `127.0.0.1:8091`. Runners containing Jev observations require the existing local `jev_systemone.py` client at the recorded path, with credentials managed outside this repository. No credentials are included.

`search.py` reads the bundled unchanged source fixtures. `expanded.py` and `local_constructions.py` run their comparison/repair experiments. `typed_local.py` keeps lexical source external and emits candidate applications, ports, positions, binders and network interfaces. Streaming events are persisted before result validation; failed/partial generations remain reviewable.

Native storage requires SBCL/ASDF and the existing Goggles checkout. The experimental `native.lisp` still targets the recorded local checkout; it is not a portable admission service. Its opaque objects and incidence holes preserve proposals, not registered meanings. Type names and licenses remain model claims.

## Boundary

The checks cover identities, references, immutable source, source operator reference coverage, interfaces and cycles. They do not prove grammatical licensing, type compatibility, scope, entailment or semantic correctness. A cleaner graph can still omit the source meaning. Future construction work must resolve those obligations rather than treat model preferences as authority.
