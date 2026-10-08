# Bounded handwritten semantic-hypergraph encapsulator

The original SHG ontology remains the target: fifteen universe collections,
eight transformation declarations, seven projections and nine invariants.
This experiment implements a **generation-zero, read-only, typed-dataflow
profile** backed by native Goggles H001/H002/A002. It does not synthesize rules,
execute the transformations, prove behavioral predicates or run providers.

## Run

Install SBCL and Git, then fetch the pinned native dependency:

```sh
./scripts/setup.sh
./shg-stack build
sbcl --script tests/check.lisp
sbcl --script tests/native-checks.lisp
./shg-stack describe
./shg-stack resolve /G
./shg-stack resolve OP
./shg-stack resolve H
./shg-stack resolve R
./shg-stack relations
./shg-stack dependencies
./shg-stack neighbors P-OUT
./shg-stack obligations
./shg-stack route R
```

`SHG_GOGGLES_ROOT=/path/to/pinned/checkout` overrides `deps/literate-goggles/`.
The pin is `99ad6709431af62dee389535ec0c62cfda40292f`. No dependency code is edited.
Every read command checks the persisted product before returning results.
`describe` returns the root address, snapshot, collection counts, registry
references and verification state. Other commands return the requested member,
relation neighborhood or obligation. `show` and `dump` are debug commands.

## Authority and construction

SHG declarations are materialized as individual H001 members. The root member
retains exact header, ontology declarations and lifecycle. Dedicated native
ports and holes retain their original constructors. The builder enumerates
all declared dataflow relations, selects/materializes them through A002, and
records their exact semantic-ID/native-relation correspondence. It derives
input/output-type and port dependencies from declaration references.

H001 is the canonical persisted structural authority. Local SHG records are
retained declarations and inspection inputs; they are not independently writable
projections. The checker reconciles every record, header, dedicated port/hole,
relation mapping and incidence, dependency, symbolic route and proof subject.
Changes require rebuilding from declarations; mutation of a saved product is
rejected when it diverges from the native snapshot.

`interpret-semantic-bundle-hypergraph-v1` and
`semantic-bundle-relation-projection-v1` provide native relation/dependency
inspection. Dependencies are a derived native projection, not an invented
sixteenth universe collection or contract-to-contract declaration.

Routes are handwritten **symbolic projections** computed from current A002
incidences and materialized in the native route registry. Both the outer route
view and native registry must equal that projection. This establishes endpoint
navigation, not R001/R002 selection authority, provider dispatch or execution.
The previous hand-selected export witness is no longer presented as a routing
guarantee; the native witness validator's limited scope remains upstream.

## Addresses and proof subjects

The `universe.addresses` records are semantic aliases retained in H001.
Full native H002 coordinates are retained separately, without dropping registry
kind, path, snapshot, facet, lineage or identity. Each coordinate must equal a
fresh reconstruction against its canonical row and closed snapshot. Missing,
additional, stale or tampered coordinates are rejected.

`proof-subjects` is the derived obligation-ID → exact H002 coordinate mapping;
`obligations` returns those coordinates. The original human-readable subject
alias must still correspond to its unchanged native member. Addresses are
constructed **after** closure and never inserted into their own snapshot hash.
This avoids digest circularity without fabricating a new address service.

## Supported semantics

Machine-readable `checks` distinguishes `:structural :checked`,
`:predicates :retained`, `:behavioral :unverified` and `:execution :unbound`.
Predicate expressions, transition guards, triggers, effect constraints and
transformation laws are retained syntax, not verified behavior. Open/unknown
obligations are allowed; proven/refuted claims and admitted/executable lifecycle
states are rejected because this profile has no verifier backend.

Supported: multiple distinct dataflow edges, nominal type equality, exact
contract/effect references, port directions/ownership, valid machine-state
references, acyclic parent references, operation-owned typed holes,
uninitialized typed memory and explicitly unbound bindings.

Each node type currently has exactly one occurrence. Ports are explicit
occurrence-owned records; reusable definition/instance correspondence is not
implemented, so shared node-type instantiation is rejected. Child graph,
primitive and none bodies, initialized values, live bindings, non-dataflow
relations, revision history and nonzero generations are explicitly outside
this profile. Parent references do not assert recursive child-body support.
Evidence records support obligations only; artifact verification needs a future
separate variant and verified provenance. No CAS claim is made.

## Evidence

`tests/check.lisp` reproduces mutation failures with exact local error categories,
checks all seven mutable address fields, verifies a second renamed fixture with
three ports/two distinct relations, and saves/reloads that fixture. It also checks
compact queries. The original review's five accepted contradictions are recorded
in `evidence/reproduction-before.log`; the corrected results and native regression
logs are retained alongside fresh-process output.

`evidence/shg-evidence.json` hashes actual repository-relative files. Regenerate
with `python3 scripts/capture-evidence.py`; no ignored local path appears in the
manifest. `working/` is rebuildable local output; committed evidence is a captured
run, not a substitute for executing the commands yourself.

`tests/native-checks.lisp` runs five unchanged upstream checker bodies for
registry, incidence, generation, address and route contracts, loading the full
system once. It avoids the upstream shell suite's repeated forced compilation.
`SHG_ARTIFACT=working/second.sexp ./shg-stack route B-R2` queries the second fixture
in a fresh process. The complete upstream thirteen-script suite is not claimed.

## Typed construction tower

The newer bounded graph-growth experiment, recorded evidence, native patch and proposed formal transaction contract are in [typed-rule-tower](typed-rule-tower/README.md). Its structural checks do not claim behavioral proof closure.
