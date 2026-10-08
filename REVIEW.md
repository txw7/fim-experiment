# Follow-up review request

Review the bounded implementation against README's supported profile and the
original SHG ontology. Do not infer full ontology semantics from retained fields.

The prior review's five contradictions were independently reproduced locally:
lifecycle admission with open proof, missing relation effect, changed proof alias,
reversed symbolic route, incompatible nominal port types. See
`evidence/reproduction-before.log`. `tests/check.lisp` now rejects those cases with
specific error categories and additionally checks exact address reconstruction,
root/rule correspondence, forged proof status, invalid state/containment/effects,
unsupported bodies/values and two distinct relations in a second fixture.

Inspect current code and actual evidence. Are there remaining ways to mutate the
outer declarations/projections while retaining a valid native envelope and pass
`shg-check`? Is relation-map correspondence exhaustive and unambiguous? Do the
exact proof-subject map and alias/native-member checks establish the intended
subject without digest circularity? Are symbolic routes fully derived from A002
incidences and reconciled with the native registry? Does the bounded-profile
contract clearly distinguish retained syntax from checked structure and proof?

Identify concrete counterexamples, missing tests and the smallest corrections.
Separate defects in the supported profile from deferred child-graph refinement,
shared node-type instantiation, behavioral verification, growth, execution,
Stack Router admission, CAS and VM/FIM integration. Source inspection is not an
independent execution; label evidence accurately.
