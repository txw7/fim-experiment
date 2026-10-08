# Hand-built semantic-hypergraph stack

Install SBCL and Git. Run `./scripts/setup.sh` once to fetch the pinned native dependency. Then:

```sh
sbcl --script ./shg-stack.lisp build
sbcl --script ./shg-stack.lisp show
sbcl --script ./shg-stack.lisp resolve /G
sbcl --script ./shg-stack.lisp resolve OP
sbcl --script ./shg-stack.lisp resolve H
sbcl --script ./shg-stack.lisp resolve R
sbcl --script ./shg-stack.lisp route
```

`build` constructs and checks the bounded, domain-agnostic fixture, saves
`working/shg-stack.sexp`, reloads it, rechecks it, and requires exact equality.
`show` reads that artifact and emits its actual SHG records. `resolve` returns
the native H002 resolution, including the actual H001 row. `route` resolves the
symbolic source/target ports and validates a native export-selection witness.

The single `SEMANTIC-HYPERGRAPH-V1` product retains all fifteen universe
collections, eight transformation declarations, seven projection declarations,
nine invariant declarations, and its lifecycle. Its envelope retains native
H001 base/generated registries and closure. Native H002 addresses index their
rows. The fixture contains a nominal type, effect, contract, node type,
occurrence, two ports, operation/open hole, two-state machine with one declared
transition, uninitialized typed memory slot, unbound provider binding, and open
proof obligation. Initial history is explicitly empty. The proof subject uses
a generation-bound semantic address whose member resolves through H002.

`SHG-*` record types and their validator are a **local extension**, not upstream
Goggles built-in types. Each source record has its own typed codec and native
member row; correspondence is checked against the emitted native row. Native
ports/holes additionally use their original dedicated constructors. A002
plans/materializes the DATAFLOW relation and its incidences. Five type/effect/
port dependencies use the existing minimum-core dependency constitution.

The route registry contains one **handwritten symbolic projection** derived
from the materialized relation and port identities. Native query/witness
validation checks selected export membership and profile. This is navigation
over actual graph objects, not an external R001/R002 acceptance receipt or an
executable route. Execution and behavioral refinement remain open.

The transformation/projection/invariant sections preserve the specification's
declarations. They are not all executable rule implementations or formal
proofs. The bounded validator checks identities, record types, references,
ports, relation endpoints, machine references, generation and unsupported
fields. Native validation checks bundle identities, registries, incidences,
closure, persistence and address resolution. Predicates are declared claims;
the code does not pretend to prove them. Child-graph refinement, revision
execution, dependency repair, and full behavioral admission are not implemented
in this bounded fixture.

Self-checks include root and object resolution, native record correspondence,
relation-role/endpoint correspondence, symbolic route endpoint resolution,
native query/witness validation, save/reload equality, and rejection of missing
objects, stale snapshots, missing types, missing exports and wrong profiles.

Native dependency: Goggles commit
`99ad6709431af62dee389535ec0c62cfda40292f` at
`deps/literate-goggles/` (or the `SHG_GOGGLES_ROOT` environment override).
The builder reuses the loader/helpers in `synthesis/working_graph.lisp` without
running its CLI. It does not edit that checkout or call a local language model.
Content identities and persistence are demonstrated; per-object CAS storage
is not claimed.

The checked-in `evidence/` contains the original local run. `working/` contains your fresh rebuild. The public repository is an experiment, not a full SHG implementation.
