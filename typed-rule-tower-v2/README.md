# Typed SHG transaction and FIM verification, v2

Native construction produced 158 → 431 addresses, 22 construction rejection checks and 431 R001 lookups. Explicit source selection, full allocation digests, persisted execution incarnations and dispatch-time budget consumption address the reviewed counterexamples. The retained second-occurrence experiment verifies identity-based selection rather than list position.

The finite Python transition experiment covers 16 states, 29 progress edges and 20 rejection edges. The original Goggles proof machine checked and deterministically rechecked strict rank decrease for all 29 retained progress edges, with no supplied axioms or closed facts. A nondecreasing edge is rejected. This proves table arithmetic; it does not prove the table exhausts the runtime or unconditional liveness. A silent worker still blocks progress.

Actual local Qwen2.5-Coder-1.5B-Base FIM attempts are retained. Whole-body and state-update fills failed. An authored guard/state scaffold narrowed the hole to the published-value expression; its second attempt returned `completion.word` and passed six Rust tests. Kani verified eleven scoped harnesses for the reconstructed candidate. The general guard check timed out (unknown). Native implementation correspondence and atomic runtime commit remain open; executable admission is blocked. The exact native operation and snapshot carry an identity-bound UNKNOWN obligation receipt, not an invented proof.

## Evidence

- `evidence/s3-contract-network.html`: interactive radial candidate-network view. Its prompt/output panel states that this graph has no recorded model calls.
- `evidence/s3-contract-network.json` and `evidence/s3-contract-prompt-trace.json`: expanded graph and explicit empty prompt trace; semantic admission remains `NOT_RUN`.
- `evidence/formal-transaction/summary.json`: scoped results.
- `evidence/formal-transaction/native-rank-receipt.sexp`: original checked theorem, program, environment and native admission receipt.
- `evidence/formal-transaction/fim/publish-expression/`: exact requests, completions, source candidates, Rust results, Kani logs and open native obligation.
- `evidence/formal-transaction/review-counterexamples.json`: executed review counterexamples.
- `evidence/formal-transaction/native-receipt-integrity.log`: newly executed upstream receipt suite, 33 checks. Its reported generic-admission residual remains visible; receipt integrity is not semantic correspondence.
- `evidence/construction-interpreter-at-run.py`: exact construction source recorded by the original result hash. Current pipeline additionally binds each construction transaction to its source, subject and parameters.

## Replay boundary

These are workstation snapshots, not a portable installer. Paths/imports expect `/home/user0/FIM`, SBCL, pinned native Goggles base `47fe6800307c8921a4b733ad6e56fa0b78698de8` plus this patch, and existing Stack Router commit `ca96fc33e7b43323f7955853750ca335710f2696`. Native rank and open-obligation adapters load original carrier/checker definitions in the minimal SHG world. A failed full-world replay is retained separately; the working path validates the exact native subject without bypassing graph checks. The frozen lookup cache is scoped to immutable validation.

```sh
rustup toolchain install nightly-2025-11-21 --profile minimal --component rust-src
python3 /home/user0/FIM/pipeline/shg_rule_tower.py
python3 /home/user0/FIM/pipeline/check_loop_transaction.py <run-directory>
sbcl --script /home/user0/FIM/synthesis/prove_loop_rank_table.lisp <run-directory>/formal-transaction/native-rank-input.lisp <output.sexp>
sbcl --script /home/user0/FIM/synthesis/retain_fim_formal_obligation.lisp <run-directory>/formal-transaction/fim/publish-expression/native-obligation-input.lisp <output.sexp>
```

Inputs retain original absolute artifact paths. Replay must restore those paths or explicitly regenerate coordinates; UUID allocations make fresh executions distinct. Rust nightly, Kani and CBMC versions are recorded in `dependency-lock.json`. Binaries, compiler intermediates and identity database are excluded. File hashes cover every packaged artifact in `package-manifest.json`.

Meta-construction remains a checked-template Python interpreter feeding native Goggles construction. Arbitrary native higher-order rule synthesis, general refinement, retries/timeouts, executable providers and FIM theorem import are not established.
