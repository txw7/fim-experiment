# Native SHG growth constructor slice

Upstream base: Goggles `6674a072521c821a3e586077d553000fb699100b`.
Working branch: `evl/shg-growth-selfhost-v1` in `/home/user0/FIM/deps/goggles-shg-growth`.

The patch adds three native constructor primitives and includes their owner in ASDF:

- `append`: checked additions through the original native bundle delta and closure owners.
- `nest`: H006 selection, typed boundary cut and extraction, retaining the child, parent delta and address correspondence.
- `enclose`: native contraction witness bound to the extracted child-member identity, plus H002 child coordinates resolved against the closed child snapshot.

SH40 synthesizes the three-capability constructor dependency program. SH39 executes it. Both are generated and activated through their original V2 admission/parity/independence gates, with their handwritten fallbacks disabled. Other runtime authorities remain bootstrap implementations. These are handwritten trusted primitive attachments consumed by generated constructor authorities; this does not demonstrate discovery or proof of new laws.

The JSON execution bridge receives content-bound invocation handles. Native objects live only in a dynamically scoped transaction staging context and remain original H001/H006 objects. Handles are not semantic addresses or a graph storage service. Semantic child coordinates are native H002 addresses.

## Run

Apply `goggles-growth.patch` to a clean checkout at the upstream base, then:

```sh
SHG_GROWTH_EVIDENCE=/tmp/shg-growth-native.sexp sbcl --script scripts/check_shg_growth_selfhost_v1.lisp
```

The check exercises a native H006 fixture, source preservation, replay, fresh transaction embedding separation, exact child expansion, address resolution and rejected stale/duplicate/malformed requests, missing prerequisite capability and constructor fallback calls. The native witness is retained separately from compact console output.

The initial slice did not construct VM controllers or register generic composition operators. Later increments below add those bounded capabilities. It does not discover new rules, establish behavioral proofs or atomically publish a graph generation. Its final status is a structural candidate with behavioral proof OPEN. It does not close the full CHECKPIN join.

See `/home/user0/FIM/runs/selfhost-growth-v1` for actual commands, logs and acceptance status. Initial execution exposed an unsupported-native-struct JSON boundary; that failure is retained alongside the corrected run.

## Earlier native algebra and binary-route increment

`shg_growth_algebra_v1.lisp` registers unary `shg-append`, `shg-nest`, and `shg-enclose` operators with the original semantic composition interpreter. Their accepted surface is `native-shg-stage`, with explicit stage preconditions, deterministic surface/identity laws, named native materializers and retained composition witnesses. The registration API now accepts custom surface kinds and core-law references; existing AFSM defaults are preserved. These are registered trusted laws, not newly discovered or theorem-proved rules.

Run `sbcl --script scripts/check_shg_growth_algebra_v1.lisp`. Its native H006 fixture exercises actual algebra execution and rejects wrong stage, wrong arity and unknown parameters. This remains a domain-independent construction fixture, not a VM coordination demonstration.

The constructor accepts an optional `symbolic-route-profile` of `source-target-v1`. After native delta application it derives route registry rows from binary CONTROL/DATAFLOW incidences in the candidate, retaining the exact relation and incidence provenance. It does not consume a supplied route table. This profile is symbolic navigation only: it grants no executable authority and does not establish argument compatibility, behavioral correctness or arbitrary hyperedge traversal. In that earlier increment routes were retained only for the appended candidate; the VM increment below adds recursive route closure. H006 still owns extraction and boundary correspondence.

Current additional evidence lives under `/home/user0/FIM/runs/native-growth-algebra-v1` and `/home/user0/FIM/runs/selfhost-growth-routes-v1`. See their receipts for actual results. That historical evidence did not establish VM-specific source matching, controller growth or recursive routed closure. The newer bounded VM checks are described below; no full VM/FIM or CHECKPIN completion is claimed.

The upstream `check_semantic_algebra_law_registry_v1.lisp` fails at `TYPED-EXECUTION-MATERIALIZES` in both this worktree and an untouched detached checkout of the pinned base. Both produce plan/product `4388A7FB` and witness `86E39B48`. The test expects the older AFSM network representation while the pinned implementation returns a generic composition product. This existing mismatch is retained in the receipt and logs; no upstream test pass is claimed.

## Native VM run-region growth

`shg_vm_growth_v1.lisp` authors the 13-function / 19-CALL seed as incomplete interfaces and native open bodies. A bounded trusted law resolves the exact native H002 run-body address and original run-to-step CALL. It produces native machine/controller/worker/state objects, phase and transition members, typed ports, body-candidate and coordination hyperrelations, request/completion dataflow, and state ownership/access relations. A002 validates and materializes every relation. The final aggregate delta retains one original predecessor; intermediate staged native checks are retained as construction evidence.

H006 extracts the grown members as one child region, producing parent boundary ports and correspondence. The optional named route producer runs inside extraction before each child/parent closure. `relation-incidences-v1` emits symbolic registry rows from all native relation roles and ordinals, with exact incidence provenance. These are navigation records, not executable provider routes.

```sh
SHG_GROWTH_EVIDENCE=/tmp/constructor.sexp \
SHG_VM_GROWTH_EVIDENCE=/tmp/vm-growth.sexp \
SHG_VM_GROWTH_VIEW=/tmp/vm-growth.json \
sbcl --script scripts/check_shg_vm_growth_v1.lisp
python3 render-network.py /tmp/vm-growth.json /tmp/vm-network.html
```

The machine has five phases and six transitions. Its native AFSM phase projection can be executed, but guards, correlation, atomic commitment, budget updates and eventual progress remain ten explicit open holes. The original run body remains open: this is an addressed refinement candidate, not an admitted implementation. The 19 original CALLs are preserved; only run's controller region is grown in this increment. Step's controller, full CHECKPIN coverage, executable admission, integer generation history, and FIM remain unfinished.

The HTML is a read-only export of native rows and incidence edges. Every exported row is resolved through the native H002 resolver against its own exact parent or child snapshot. The renderer creates no semantic graph objects. Inspectors expose row identity, H002 identity and original native row content; snapshot headers identify each native bundle.

Actual final acceptance: `evidence/vm-run/fresh-check.log` ends with `SHGVmGrowthV1Green` and exited 0. The export resolves 313 native addresses; parent and child contain 21 and 13 symbolic route rows respectively. See `evidence/vm-run/receipt.json` for exact commands, source pins, hashes, bounded guarantees and retained failures. `evidence/vm-run/network.html` is the new interactive network.

## Connected H006 boundary inspection

The newer `evidence/boundary-view/network.html` includes the two actual H006 parent/child mappings and their endpoint projections, giving six inspection links. Amber lines are boundary correspondences, not CALL or execution edges. Click a line for its addresses, direction, contract and correspondence identity; the full native witness is expandable. The child enclosure can be collapsed and expanded.

`SHG_VM_GROWTH_VIEW=/tmp/connected.json sbcl --script scripts/check_shg_vm_boundary_view_v1.lisp` reads the retained native artifact (set `SHG_VM_ARTIFACT` to its path), resolves endpoints with H002, checks source/successor incidence correspondence and port contracts, and rejects a dangling mapping. It does not alter the semantic graph. Snapshot, row and original-incidence equality against the earlier export and both boundary-crossing navigation paths were checked separately. Browser checks exercised the inspector and expand/collapse controls. See the boundary-view receipt for exact scope and hashes.

## Joint run/step growth

`shg-vm-joint-growth-v1` invokes the bounded run law and stages step coordination before returning one combined addition program against the original predecessor. The starting 13 function declarations and 19 CALL requirements remain authored. The fixed law supplies the fetch/decode/execute sequence; Goggles does not discover that architecture or this rule.

The native result has two controller definitions, four source-linked call coordinations, two machine definitions, nine phases, thirteen phase transitions, 36 grown members and 22 open holes. Both controllers live in one extracted child coordination region. Native A002 materializes the ordered serial relation, nominal request/completion channels, source CALL proxies and state ownership/access. H006 derives six boundary mappings; H002 resolves 521 rows. The route registries have 25 parent and 33 child rows, with symbolic authority only.

The step phase projection has fetch/decode/execute/done phases; typed outcome propagation, correlation guards, commit and new-request reset remain open obligations. Its seven phase transitions and the existing six run transitions were executed as native AFSM projections. These checks do not establish implementation correctness or VM execution. No FIM or executable provider was admitted.

Run `sbcl --script scripts/check_shg_vm_joint_growth_v1.lisp` with `SHG_JOINT_EVIDENCE` and `SHG_JOINT_VIEW` paths. The driver also reruns the prior run-only/self-host checks. To inspect a persisted result, set `SHG_VM_ARTIFACT` to the native artifact and run the boundary-view checker. The latter now handles either run-only or joint scope. The compact export retains witness references and exact endpoint coordinates instead of repeating the entire address map on every link.

Newest artifacts: `evidence/joint-growth/network.html`, `receipt.json`, `native.sexp` and the actual check logs. The receipt distinguishes authored inputs, native generated products, phase checks and open semantic guarantees. The old evidence is retained as historical evidence.
