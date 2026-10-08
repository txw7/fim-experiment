# Bounded loop and FIM transaction V2

Implemented: explicit subject selection from a pinned native index, full declaration/index digest binding, durable execution-incarnation and construction-namespace reservations, transaction binding checks, full SHA-256 fresh allocation suffixes, dispatch-time budget accounting and explicit exhaustion. SQLite UUID reservations provide collision detection; mathematical global uniqueness or crash recovery of pending runtime state is not claimed.

The meta-constructor remains fixed-template Python code. Native higher-order rule construction is not established.

## Evidence scopes

- Native structural build, reload, replay and address lookup are Goggles checks.
- The bounded model comparison enumerates initial budget 0..2, word 0/1, all three completion statuses, one incarnation per model and monotone iteration IDs. It checks every reachable progress edge and five correlation-mismatch observations at Waiting states. It is not an unbounded theorem or a proof for all runtime schedules.
- The silent-worker trace demonstrates why unconditional liveness is false. Retry and timeout semantics are unsupported.
- A real raw local Qwen FIM request targets a proposed Rust completion helper under the exact native controller operation address. The helper is not yet a native admitted realization. Source digest, range, model digest, prompt, raw completion, candidate digest, compiler output and tests are retained. Three whole-body candidates failed tests; none was admitted.
- Kani is a separate implementation checker. Its harness bounds initial budget to 0..2, phase to Ready/Waiting/Terminal, pending to the current key or none, committed length to 0/1, and incarnation strings to a/b. Numeric key fields and words are symbolic full-width values. Kani evidence is bounded by this harness, not a theorem for arbitrary input containers or strings.
- The handwritten Kani control is explicitly not model-generated.

## Existing native authority

`formal-proof-receipt-v1-admission-row` remains the formal admission boundary. The local evidence-integrity checker does not manufacture native proof receipts or claim proof closure. The native 33-check receipt-integrity regression is executed independently; its A002 fixture is not this loop's proof. Original semantic projection/correspondence must establish what a theorem covers; receipt identity alone is insufficient.

The FIM native gate consumes no implementation receipt because none exists and confirms the original owner rejects missing proof. Implementation correspondence, atomic/durable runtime commit, general liveness and executable admission remain open/blocked.

## Commands

```sh
python3 ~/FIM/pipeline/shg_rule_tower.py
python3 ~/FIM/pipeline/check_loop_transaction.py <run>
python3 ~/FIM/pipeline/fim_completion_transaction.py <run>
kani <run>/formal-transaction/fim/candidate-kani.rs --harness completion_contract --output-format terse
kani <run>/formal-transaction/fim/handwritten-control-kani.rs --harness completion_contract --output-format terse
sbcl --script ~/FIM/synthesis/check_fim_proof_gate.lisp <run>/formal-transaction/fim/native-gate-input.lisp
```

The required Kani toolchain is nightly-2025-11-21 with rust-src. Recorded hashes and outputs, not this document, establish individual command outcomes.

## Executed refinement result

Whole-body and state-update FIM attempts failed. Further authored lowering fixed the guard and phase-update scaffold and left the publish-value expression as the FIM span. Qwen returned `completion.word`; the reconstructed whole Rust file passed six tests. Kani verified its accepted-state update harness and ten fixed rejection-case harnesses. These are eleven scoped verification successes, not an unbounded contract proof. The broad mixed guard harness timed out and remains unknown. The broad handwritten control ended with exit 143 and no verdict, also unknown.

The exhaustion transition is represented and the protocol transitions to terminal with zero budget. Its executable termination-effect input construction remains part of the open state/effect correspondence obligation: a machine declaration and protocol phase update do not establish a complete effect realization.
