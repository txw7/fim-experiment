# Bounded typed SHG construction tower

Recorded implementation and evidence: checked template → generated typed rule → structural admission → addressed seed match → fresh identities → native Goggles successor → bounded protocol trace.

154 seed addresses become 421 successor addresses. Recorded checks: 22 negative checks, 27 upstream checks, and 421 R001 lookups. Behavioral refinement and liveness proofs remain open. No executable provider or VM instruction execution is claimed.

- [Interactive native graph](evidence/network.html) — download/open locally.
- [Implemented contract](spec/typed-coordination-rule-tower-v1.md)
- [Next formal transaction contract](spec/formal-construction-transaction.md) — specification, not implemented proof machinery.
- [Exact result](evidence/result.json), [rule receipt](evidence/rule-admission.json), [graph receipt](evidence/graph-admission.json).

## Source and replay boundary

The pipeline files are exact workstation source snapshots, preserving original paths and imports. This is not a portable installer. They expect the documented `/home/user0/FIM` layout, SBCL, the pinned Goggles checkout plus `goggles.patch`, and the existing Stack Router `h002_file_lookup` binary. The native base is `47fe6800307c8921a4b733ad6e56fa0b78698de8`; router commit is `ca96fc33e7b43323f7955853750ca335710f2696`. Apply the patch to a clean native base with `git apply goggles.patch`.

Original run commands:

```sh
python3 /home/user0/FIM/pipeline/shg_rule_tower.py
python3 /home/user0/FIM/pipeline/shg_typed_web.py <printed-run-directory>
```

Evidence keeps original absolute paths for provenance. `upstream-regression/check.log` is the earlier executed run against the same native source hashes, not a freshly rerun regression. The original evidence manifest is preserved; `package-manifest.json` hashes the actual packaged paths.
