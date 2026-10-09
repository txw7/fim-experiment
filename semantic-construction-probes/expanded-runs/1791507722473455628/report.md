# Expanded construction probe

Three unchanged source inputs. Two independent initial proposals attempted per input; each completed initial proposal received a paired feedback repair. Ten requests were made: eight completed, two initial requests timed out, and their two repair slots were not run. Limits increased from 8 objects/5 relations/1,300 completion tokens to 40 objects/48 relations/6,500 tokens. These are diagnostics, not an accuracy benchmark: no gold graph or semantic-law admission.

| Source | Candidate | Objects/relations | Structural errors | Occurrence warnings | Networks | Network operands | Relation operands |
|---|---|---|---|---|---|---|---|
| comparison | initial-29 | 4/1 | 0 | 0 | 0 | 0 | 0 |
| comparison | feedback-29 | 6/5 | 2 | 0 | 0 | 0 | 0 |
| inference | initial-17 | 2/2 | 4 | 0 | 0 | 0 | 0 |
| inference | feedback-17 | 12/7 | 24 | 0 | 0 | 0 | 0 |
| recursive | initial-17 | 8/6 | 3 | 2 | 0 | 0 | 0 |
| recursive | feedback-17 | 10/5 | 0 | 0 | 0 | 0 | 0 |
| recursive | initial-29 | 12/8 | 2 | 0 | 0 | 0 | 3 |
| recursive | feedback-29 | 12/8 | 2 | 0 | 0 | 0 | 3 |

A network count alone does not establish semantic synthesis. All proposed operator and relation meanings still require native validation. Laya classifications are accepted only when the service reports no dropped state or truncated questions. Independent proposals use temperature 0.55 with distinct seeds; their independence is procedural, not statistical.

## Observed repair effects

Recursive seed 17: structural errors 3 → 0 and occurrence warnings 2 → 0. However, the repair removed the operator structure: all ten objects are entities and the five relations are simple attachments. It omits WHAT and both WHEN occurrences. This is structural cleanup by semantic omission, not a successful interpretation.

Recursive seed 29: both candidates have two structural errors, and three relation-as-operand references. Example r5 takes r1 as its temporal operand. This demonstrates generated higher-order reference syntax, but the malformed graph and unregistered meanings prevent admission.

Comparison seed 29: errors 0 → 2; feedback invents unanchored capacity and limit entities. The initial proposal omits the degree comparison.

Inference seed 17: errors 4 → 24; feedback worsens member-reference validity.

All four compact Laya requests completed without truncation: unsupported, unresolved, unsupported, supported respectively for recursive-17, inference-17, comparison-29, recursive-29. These refer to a single proposed relation each, not a graph-level verdict.

Zero network objects or network operands across all eight completed candidates. No native semantic admission attempted.
