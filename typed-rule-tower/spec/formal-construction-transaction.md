# Formal construction transaction — proposed next increment

Status: specification. Obligation closure checking and exhaustive model checking are not implemented by the recorded tower.

Each application stages a delta of added, removed and preserved objects; parent/child port, state and effect correspondence; exact rule bindings and guards; source generation and input digests; an obligation ledger; and evidence for checks actually performed. Structural acceptance permits inspection, not execution. Parent contract and policy select execution gates.

## Evidence and closure

Every receipt identifies the proposition and interpretation, exact native subject and snapshot, instance-versus-rule scope, assumptions, model domains/bounds, implementation/model correspondence, checker version, input/output digests, evidence kind, dependency receipts and reuse conditions. Evidence kinds distinguish tests, exhaustive finite checks and checked theorems. Status is open, proven, refuted or unknown.

Closure independently checks required evidence, identity, scope, version, assumptions and recursive dependencies. Open, unknown, refuted, stale, missing or out-of-scope blocking obligations prevent closure. Historical receipts remain about their historical subjects. Carry-forward needs checked frame/dependency correspondence. Registry closure alone does not establish proof closure.

## Single-flight model

Protected state: phase Ready/Waiting/Terminal; nonnegative remaining dispatch budget; optional pending activation identity; committed identities; pinned graph/contract generation.

Dispatch from Ready with positive budget allocates a never-reused identity, consumes one budget unit, records pending, and enters Waiting atomically. Completion accepts only a typed result matching identity, generation and correlation scope; commits at most once, clears pending and returns to Ready or terminates. Rejected stale, mismatched and duplicate observations preserve protected state, though audit logging may change. Ready with zero budget terminates explicitly.

Invariants: Waiting has exactly one pending activation; other phases have none; identities are never reused; each identity commits at most once; rejection preserves protected state; accepted transitions preserve boundary/state/effect contracts. These are per occurrence.

The existing demonstration must be aligned with dispatch-time consumption and explicit exhaustion before evidence is reused. Runtime atomic/durable commit correspondence is a separate open obligation. At-most-once commit does not establish exactly-once external effects.

## Liveness

Ranking: Ready(r)=2r+1; Waiting(r)=2r+2; Terminal=0. Dispatch and accepted completion decrease the measure; rejection and waiting need not. Termination requires eventual matching completion and fair service, or a specified non-starvable timeout/cancellation path. Retries consume finite allowance. Failure termination and successful completion are distinct claims.

## First acceptance

Retain an explicit transition model, exhaustive finite-check configuration, checker results and counterexamples. Exercise normal completion, wrong correlation, duplicate completion, stale generation, zero budget, exhausted retries and a nonresponding worker. Check successful completion and termination reachability to exclude vacuity. Structural, behavioral and liveness closure are separate results; runtime correspondence remains open until established. Rule-level proofs must cover admissible substitutions and contexts, not merely one instance.
