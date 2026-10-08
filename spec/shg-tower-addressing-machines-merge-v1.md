# SHG tower, recursive addressing and machines: merge specification V1

Superseded by [co-grown SHG specification V2](co-grown-shg-tower-spec-v2.md). The Catlab authority transfer in section 3 is withdrawn.

Status: proposed integration contract, source-inspected on 2026-10-08. This document specifies a merge of capabilities; it does not claim an implemented bridge, completed acceptance, executable VM or a Git branch merge.

## 1. Objective and acceptance boundary

Combine native Goggles/SemAlgebra synthesis, the pinned local SHG handoff, the bounded construction/FIM transaction experiment and the SS/SR recursive execution machinery. Produce a recursively typed SHG whose operations, ports, hyperrelations, incidences, machines, transitions, guards, effects, bodies and obligations are individually resolvable. Grow addressed open regions through checked graph transformations. Lower only regions with sufficiently resolved semantics into digest-bound source holes. Enroll executable realizations only after their applicable admission gates pass.

The authoritative target remains the supplied semantic-hypergraph ontology: all 15 universe collections, eight transformations, seven projections, nine invariants and eight lifecycle labels. The 98-sort receiving schema is its implementation candidate, not permission to omit ontology sections. An ontology coverage ledger must map every collection and required field to native sorts/links, explicitly unresolved obligations or a named schema extension. A textual payload is not implementation of its semantics.

First acceptance is structural synthesis, typed machine representation, one bounded interpreted machine, recursive address correspondence, checked revision and a source-bound FIM transaction. General VM execution, arbitrary effects, new-rule discovery, full self-hosting and unconditional liveness are not prerequisites. Structural acceptance must remain distinct from behavioral proof and executable activation.

## 2. Pins and inspected evidence

| Component | Exact source | Meaning |
| --- | --- | --- |
| Local handoff | `txw7/orchestration@7b66ecc9b717361b00bd833d391fafd0c5db40ab`, `work/alignment/shg-local-handoff-v1` | Frozen 98-sort Catlab SHG, DPO mutation, typed queries, supplied VM lift, offline FIM gates and integration notes |
| Goggles implementation candidate | `txw7/literate-goggles@6674a072521c821a3e586077d553000fb699100b` | Current locally inspected native synthesis/algebra source; full exact-head acceptance not rerun here |
| Handoff Goggles reference | `a14ed476406700d1078daa1d3004f2a09ec459db` | Historical producer inspected by the handoff; not silently substituted for current HEAD |
| SS/SR | `txw7/egress-stacks@0a48afc66ca24b94ba93cbcb40c82bdf6a1ee76a`, PR #47 | Recursive source headers, scope exports, native routing, callable realization and host activation |
| Existing transaction experiment | `txw7/fim-experiment@82c83a494fe158bf2d05143b3f891793a5681572`, `typed-rule-tower-v2` | Bounded template interpreter, native SHG fixture, source selection, identity reservations, finite checks, actual FIM and scoped proof evidence |
| Original inert bridge | `txw7/egress-stacks@0041fa900e3d3bcf92215e5de81ccf47c2f183e4` | Handoff's pinned declaration-export producer; not live routing authority |

Fresh inspection checked all 76 entries in handoff `SOURCE_PINS.json`, with zero mismatches. The following four producer blobs are identical at the historical reference and current Goggles pin:

| File under `lisp/` | Git blob |
| --- | --- |
| `l7_sparse_system_synthesis_v1.lisp` | `1aa00029d5fd9cd35cb63820de16dcdc710005cf` |
| `semantic_algebra_recursive_goal_witness_v1.lisp` | `d91a874515def4fa344dfe45787c5ebdd17c6dfa` |
| `l7_semantic_system_product_v1.lisp` | `bc534a426ddabdac55c665f5a815566b19b1f6bc` |
| `l7_interfunction_relation_synthesis_v1.lisp` | `4499bee2c668b37c345e40276b95cb00316ada56` |

This four-file comparison is not proof that the entire transitive dependency closure is unchanged. Implementation must retain the complete effective source closure and rerun appropriate gates at the selected pins.

Handoff native/test success counts are historical receipts. Its VM lift has 13 supplied functions, 19 supplied calls and zero concrete value-DATAFLOW edges. Its fetch Rust fixture is authored, not synthesized, and runtime Rust checks were NOT_RUN in its packaging environment. PR #47's checked-in runtime and receipts were inspected; its 47 regression checks were not rerun for this specification. Existing v2 rank proof covers retained table arithmetic only; eleven Kani checks cover explicit harness scopes, not universal implementation refinement.

## 3. Authority and repository ownership

The SHG is semantic authority. In this integration profile, the handoff's Catlab representation is the retained graph owner after import. Goggles native products, H001 bundles, H002 coordinates and search witnesses remain immutable producer evidence and resolvable provenance for that imported generation. They do not become a second independently editable copy.

SS source headers, compiler products, route images, packed IDs and binaries are derived realization artifacts. A body can be addressable and OPEN without an executable binding. A graph may retain several interpretations without selecting an executable interpretation.

Retain the existing v2 experiment as a regression/reference lane. Do not replace the 98-sort graph with its narrower local SHG schema. Do not call deterministic VM elaboration or Catlab import topology synthesis.

Initial new integration code belongs in `fim-experiment/shg-integration-v1/` (proposed). Use explicit configured checkout paths; do not copy upstream runtimes and create new authorities. Suggested modules are `goggles_capture.lisp`, `product_to_shg.py`, `correspondence.py`, `machine_profile.py`, `runtime_enrollment.py`, `run.py`, fixtures and tests. Each is an adapter to the owners below. Port changes upstream only when a concrete missing owner API is established.

| Concern | Existing owner to reuse |
| --- | --- |
| Goal synthesis | Goggles `synthesize-l7-sparse-semantic-system-v1`; native `plan-semantic-algebra-goal-v1` |
| Control search and lawful composition | `semantic_algebra_*`, registered constitutions, decomposition laws and native search scheduler |
| Product validation | `validate-l7-semantic-system-product-v1`, synthesis/search witness validators and hierarchical carrier/persistence validators |
| Hyperrelations | A002 planning/materialization and ordered role-bearing incidences |
| Native bundle/address evidence | H001 closure/registries; `make-semantic-bundle-row-address-v1` and native resolver |
| Retained SHG | Handoff `base/native/src/SHGCore.jl`: import/validate/export; frozen schema; generic Lisp codec |
| SHG revision | `SHGMutations.jl` and existing attributed DPO mutation path |
| SHG queries | `base/typed_query.py`, entity/typed-row coordinates, field coordinates and checked scope/boundary traversal |
| Source and runtime routing | SS recursive enrollment/header owners; SR `resolve_recursive_route_request`; generated callable runtime |
| Formal evidence | Goggles original proof checker/rechecker, formal receipt admission and selective invalidation |
| FIM materialization/gates | Handoff preparer/candidate gate; existing v2 raw local-model adapter and exact-range insertion |

## 4. Native synthesis into retained SHG

The producer receives a finite primitive catalog, goal, contracts, state/resource/authority constraints, allowed effect scope and explicit recurrence/routing requirements. It must not receive the completed output topology, emitted addresses or fabricated proof results.

Call `synthesize-l7-sparse-semantic-system-v1` and retain all five returns: product, synthesis witness, control-search witness, relation evidence and theorems. Independently validate their exact identities and the carrier closure before translation. State/resource/authority/effect-order relation inference is supported only in the producer's declared domain; ambiguity remains explicit.

A new versioned product-to-SHG adapter must translate:

- Hierarchical carriers into Graph/Interior/Occurrence, preserving sharing and ownership.
- Reusable definitions and occurrence instances into distinct native declaration/instance records.
- Operation interfaces into Operation/OperationInstance/Body and typed definition/instance ports.
- Relation constitutions into RelationType/Role; applications into Relation and ordered Incidence. Preserve n-ary roles, multiplicity, correlation and relation-to-relation endpoints.
- Actual state declarations and accesses into typed Memory/Coordinate/StateAccess records where semantics exist.
- Declared effects and contracts into native typed links and obligations.
- Actual machine semantics into StateMachine/MachineState/Transition and association records; never infer transitions from an ownership relation.
- Unresolved content into stable Slot/SlotState/Hole/Obligation records with expected native kinds and value types.

Imports of shared catalogs are read-only. Child interfaces cross only checked BoundaryMaps. The adapter must never clone a shared declaration or flatten a hidden child port to satisfy a reference.

Apply import/validate/export and codec round-trip through the existing native SHG owners. Emit a bidirectional correspondence witness: every supported source object has an accounted target, every derived target has a source or registered derivation law, and incidence positions/roles agree. Rejected/unsupported source fields cannot disappear into opaque Value records.

Attach the candidate to its selected Body/Interior using the existing mutation path, exact source pin and delta. Retain predecessor and candidate; no in-place mutation of the archival fixture.

## 5. Recursive hyperaddressing contract

Do not unify incompatible coordinate formats by equal names or one digest.

1. **Goggles source coordinates:** retain complete H002 occurrence path, bundle snapshot, registry kind, row/facet/lineage and address identity. Reconstruct and resolve against the pinned native closure.
2. **Canonical SHG coordinates:** use handoff graph generation/content/schema pins and exact entity/typed-row coordinates. Field coordinates retain parent coordinate, schema hash, field, RFC6901 pointer and value hash. Validate through existing typed readers.
3. **Source realization coordinates:** retain SS recursive source address, parent boundary, signature, source/body/header/bundle digests and exact enrollment fields.
4. **Executable coordinates:** retain SR addressed query/scope frames, consumer/profile/traversal authority, selected export, realization and activation digest.

Define `SHG_ADDRESS_CORRESPONDENCE_V1` as a proposed integration record, not an existing upstream schema. It binds full coordinates, their exact source pins, member kind and a named correspondence law/check receipt. Semantic membership correspondence may be one-to-many for declaration/instance elaboration. Only a concrete selected operation realization may acquire an executable binding; require its exact signature and admitted body.

Root, nested Graph, Body, Hole, Port, Relation, each Incidence, MachineState, Transition, Guard, Effect and proof subject must resolve independently. Relations are addressed objects, not just drawn lines. Hyperrelations whose participants include other relations must preserve that endpoint identity.

Recursive navigation follows native ownership, imports, exports and boundary maps. Literal string-path concatenation is not access permission. Resolve every intermediate boundary, reject missing/ambiguous/stale coordinates and retain the traversal witness. Root generation and nested graph generations must be separately represented; a scoped map pins the complete involved snapshot set rather than assuming every child has the same number.

PR #47's `scope::export` is the callable-facing coordinate, not a complete address of all graph members. Its fixture-local packed namespace and hash-based surface slots must retain collision rejection; this merge makes no global ID allocation claim.

Hash ordering: close the semantic graph first; construct external address-correspondence and realization manifests against that immutable graph. A manifest must not participate in the hash it contains. If correspondence is later stored inside SHG, refer to a separately identified predecessor/source pin and recompute the successor explicitly.

## 6. Machines, typed effects and runtime state

Represent machines with existing native StateMachine/MachineState/Transition, TransitionGuard, TransitionOperation, NodeMachine and OccurrenceState links. Guard expressions must have checked operand/result types and explicit reads. Correlation schemas and state accesses resolve to actual native members.

The frozen schema's `Transition.event` is Text, not by itself a typed event reference. A proposed machine-profile correspondence must resolve each event token to an exact ValueType/contract and validation rule. Missing event typing blocks interpretation. If intrinsic typed-event links are required, propose a versioned schema extension and migrator; do not silently change the 98-sort schema.

Transition effects require exact scope. A whole-operation effect set does not prove a transition's narrower set. Represent transition actions through distinct declared operations where supported, or require an explicit checked transition-to-action/effect correspondence. The v2 zero-budget path's completion-consuming terminate effect remains an unresolved mismatch until exhaustion has a lawful input contract.

First interpreted profile is a single-flight, fuel-bounded call loop:

| Event | Preconditions | Protected update |
| --- | --- | --- |
| Issue | Ready, fuel > 0 | Reserve fresh activation; consume fuel; set pending; enter Waiting |
| Matching completion / continue | Waiting; exact generation, incarnation, invocation, iteration, attempt; typed result; fuel > 0 | Commit once, clear pending, update carried state, return Ready |
| Matching completion / stop or halt | Same correlation/type gate; applicable exit guard | Commit once, clear pending, publish permitted result, enter terminal state |
| Matching completion / trap | Same correlation/type gate; trap guard | Apply declared trap preservation policy, clear pending, terminate |
| Exhaust | Ready, fuel = 0 | Terminate without fabricated worker completion |
| Wrong/stale/duplicate observation | Any failed matching/readiness condition | Protected state unchanged; audit may record rejection |

Activation identity includes a durable execution incarnation, pinned machine/graph generation, invocation, input generation, iteration and attempt. Never restart counters in a namespace that permits old completions to match. Immutable graph state is distinct from runtime phase/pending/commit state.

Interpret only a versioned, admitted profile. Catlab currently stores/validates machines; it is not a general machine executor. The v2 Protocol supplies a bounded reference implementation, not universal semantics for every SHG transition. A general executor must consume the graph's checked transitions, rather than maintain an unrelated Python machine decorated with graph rows.

For wait/join, require same snapshot/input generation/correlation, all required typed observations, a checked guard, duplicate handling and one accepted activation identity. Fan-out has explicit child activation identities and join membership. Missing results leave readiness false. Conditional progress or timeout semantics must be declared; finite fuel alone does not prove termination while Waiting.

State/effect edges remain distinct from call and control edges. A relation linking state owners is not a read/write implementation. Each runtime state access has ownership, consistency and commit semantics. EffectIntent/Activation/Return/Commit records are retained declarations until a verified lifecycle owner exists. The durable external effect lifecycle stays with its existing owner; do not infer exactly-once external execution from at-most-once result commit.

## 7. Construction driver and candidate retention

Register finite construction laws for function scope, argument/result binding, branch alternatives, call activation/continuation, sequence, fuel-bounded loop, async dispatch and join. Each law states typed match/parameter/fresh binding classes, allocation scope, construction program, boundary/effect preservation requirements and admission obligations.

Use SemAlgebra's operator/topology/parameter search and recursive reuse. Do not build a parallel general optimizer. The current recursive planner selects a solution, and relation-goal planning requires exactly one admissible constitution. Therefore the requested `publish without selecting interpretation` needs an explicit alternative-retention interface, not a renamed selected result. Retain candidate DAGs and rejection evidence while guaranteeing no executable selection for ambiguous candidates. If the existing planner cannot expose alternatives without selection, add a bounded owner API and verify it; do not claim current support.

Each construction transaction returns exact bindings, source pin, rule/registry identities, graph delta, boundary correspondence, obligation ledger, check receipts and successor pin. Rejected candidates remain evidence; context-required candidates suspend with named missing inputs. Rejection must consume attempt budget.

Initial integration limits: depth 8, 128 occurrences, 512 relations, 4096 added native records per transaction, 16 candidates per goal and 256 expanded goals. Loop demonstration fuel is 0..2; retry count is zero; live provider count is zero. These are proposed limits checked by the driver, not claimed existing producer options. The sparse wrapper does not expose the planner's budget keyword: verify defaults or add explicit owner budget plumbing before claiming these limits govern native search.

## 8. Lowering, FIM and executable enrollment

Resolved semantics lower progressively: coarse structure → typed calls and effects → operation/state/control graph → source AST/signatures → exact source span → candidate body. Unknown VM widths, encodings, traps, aliasing or effect order remain holes. No FIM request may choose those semantics implicitly.

Reuse handoff typed-lowering contracts and native compiler owners with explicit correspondence. Existing protocol→AFSM→compiler IR and CFG/SynthSlotPlan/IR1 functions do not establish automatic compatibility with every SHG product. Preserve the distinct direct CompilerIR/SynthSlotPlan route and bounded IR2/CFG route.

A FIM request binds graph/schema pins, exact OperationInstance/Body/Hole coordinates, source digest, UTF-8 half-open byte range and preimage, AST role, helpers/types/contracts, permitted effects and verification policy. Prefix/suffix come from the exact current source. Model input is code context; graph ownership and admission remain tool-side. Recheck preimage before insertion and preserve every byte outside the authorized span.

Compile/test/prove candidate as required. Passing finite tests does not mark semantic obligations PROVEN. Attach supplied code using native mutation and BodyCode/source correspondence; DEFINED and VALIDATED remain distinct. Recompute affected dependencies and address maps. FIM realization is a downstream projection of the retained graph.

PR #47 currently admits only `(x: i64) -> i64` native callables, no nonlocal captures or arbitrary effects. Reproduce its three-function slice unchanged first. A separate typed callable ABI extension is required before enrolling stateful VM or string-returning classify/print functions. Do not fake compatibility with casts or erased JSON.

Enroll lawful source/header/export/realization bindings using existing SS/SR producers. `prepare` must preserve active code; `activate` must require expected predecessor, artifact hashes and closed required gates. Host activation atomicity is not a proof that arbitrary machine transitions or external effects commit atomically.

## 9. Proofs, receipts and closure

Reuse original Goggles proof checking, deterministic rechecking, formal admission and selective invalidation. Every receipt binds exact subject coordinate, source/target pins, rule/registry, proposition, assumptions, verification method/version, domain/bounds, dependency receipts and artifact hashes.

Separate these gates:

- Structural: native typing, scopes, identities, ordered incidences, references, boundaries and complete correspondence.
- Machine safety: pending-phase consistency, no identity reuse, at-most-once result commit, rejected-observation immutability, declared state/effect updates.
- Behavioral preservation: predecessor/candidate and graph/implementation correspondence for the actual contract.
- Liveness: progress under explicit fairness/completion assumptions, or a verified timeout/cancellation policy.
- Executable: all blocking claims plus actual callable/router/runtime compatibility and activation integrity.

The v2 rank theorem is reusable only for its exact retained table arithmetic proposition, or after checked correspondence derives a new table. Kani tests are external bounded evidence until an independently checked native import/correspondence exists. Presence of an artifact ID or a generic receipt cannot establish the proposition's semantic correspondence.

Closure rejects open/refuted/unknown/stale/wrong-scope blocking obligations and recursively validates dependencies. Assumptions stay visible. Timeout is UNKNOWN; missing tool is NOT_RUN. Type/rule/source changes invalidate dependent current applicability; historical receipts remain valid for their historical subjects. Reuse unaffected evidence only through a checked frame/dependency correspondence.

## 10. Ordered implementation and quantified acceptance

| Milestone | Deliverable | Required checks |
| --- | --- | --- |
| M0 | Pins, ontology/schema coverage and clean isolated integration lane | All source hashes; upstream provenance; no edited shared worktree |
| M1 | Goggles native producer capture and validation | Genuine goal/catalog→product; all five outputs; goal perturbation changes or rejects product |
| M2 | Product-to-98-sort adapter and native successor | Complete supported object/role correspondence; shared identities; codec round-trip/native reconstruction |
| M3 | Recursive address correspondence | Root, two nested boundaries, all member families and fields resolve; stale/foreign/private lookup rejected |
| M4 | Bounded machine profile and interpreter correspondence | Fuel 0..2, normal/halt/trap, wrong correlation, duplicate, stale generation, zero budget, silent worker; reachability and safety evidence |
| M5 | Construction alternatives and checked revision | At least two retained candidates without execution selection; second eligible occurrence explicitly selected; rejected transaction preserves source |
| M6 | Typed source/FIM seam | Reference accepted, increment-before-bounds mutant rejected, stale source/span rejected; actual model candidate retained separately |
| M7 | SS/SR realization slice | Reproduce three-function runtime; nested delegation, stale activation, binary mutation, prepare preservation and recovery checks |
| M8 | Integrated proof/admission report | Exact evidence closure, unresolved claims visible, no executable admission for open blocking obligations |

Fixtures:

A. `classify` is source-backed: two mutually exclusive returns, argument→parameter binding, selected return→call result→assignment→print. Print is a declared but unbound output effect; no live output provider is invoked. String return is outside PR #47 ABI, so execution is blocked until a checked extension exists.

B. Bounded controller/worker loop with a typed request/completion pair, explicit correlation and state/effect contracts, nested Body and addressed machine.

C. The handoff's 13-function/19-call VM is a supplied-topology regression. Recover it from native relations/boundaries. Keep DATAFLOW unresolved until actual value/state semantics are supplied; do not turn CONTROL_ORDER into CALL.

D. PR #47's three nested i64 functions exercise executable realization only, not full VM semantics.

Positive checks P01–P14: all ontology sections accounted; native synthesis witness; role/position preservation; shared definition/distinct occurrence; child boundary correspondence; root/member/facet/field resolution; source→SHG→header/export correspondence; complete machine associations; exact transition interpretation within profile; alternative retention; one-generation DPO revision; FIM exact-span enforcement; lawful recursive callable execution; fresh-process persistence and recovery.

Negative checks N01–N18: duplicate identity; malformed incidence tuple; incompatible type; foreign port ownership; missing boundary export; flattened private access; wrong scope; stale graph/schema pin; changed H002 coordinate; wrong source/header/body pin; unknown explicit route ID; mismatched/duplicate completion; transition/effect mismatch; unsupported event/ABI; fabricated proof; stale dependent receipt; changed binary; wrong activation predecessor. Assert expected error categories, not merely any failure.

No gate may substitute supplied serialized topology, a count banner or a full debug dump for actual native records/resolver/checker outcomes. The HTML graph is a projection of the admitted structural snapshot and exposes real typed fields and coordinates; it is not acceptance evidence by itself.

## 11. Commands and evidence package

From the pinned handoff root, existing gates are `scripts/check-local.sh offline`, `native-shg` and `native`; run full native mode when its prerequisites exist. Keep newly executed receipts separate from historical packaging receipts. Run the FIM `verify_fim.py self-test` with an available pinned Rust compiler; `--python-only` cannot satisfy runtime acceptance.

From pinned egress-stacks, the existing runtime reproduction is:

```sh
cargo build --offline --manifest-path synthesis/stack-router/Cargo.toml \
  -p stack-router-registry-kernel --bin stack-router-recursive-cli \
  --target-dir <fresh-router-target>
python3 synthesis/stack-synth/scripts/check_nested_callable_runtime_v1.py \
  --native-cli <fresh-router-target>/debug/stack-router-recursive-cli \
  --output <fresh-runtime-output>
```

Use original Goggles focused search/product/formal gates at the exact selected pin. Its full exact-head algebra harness requires a clean checkout. Do not claim the copied four-file producer comparison replaces it.

Each integration run retains input, pins/effective source closure, product and all witnesses, native SHG snapshots, before/after deltas, address correspondence, machine-profile/model/runtime traces, candidate/rejection/context records, source maps and exact FIM payloads, check/proof receipts, header/export/realization enrollment and scope traversal witnesses, gate policy/closure and a path-consistent SHA256 manifest. Capture exact commands, tool versions, exit statuses and bounds. Compact handles and queries are the normal interface; complete serialization remains a diagnostic/replay artifact.

Implementation completion requires M0–M8 for these bounded fixtures, with open behavioral/liveness claims honestly blocking their corresponding gates. This specification authorizes no implicit live effect, global ID allocation, schema migration, executable VM admission or automatic merge of upstream branches.
