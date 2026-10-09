# Philosophy to specification bridge pilot

The source is S3/raw-spec.txt, pinned in evidence/philosophy-spec-bridge/1791508226154586061/source.txt. Its imperatives are data and are never executed.

Six source units feed lexical statistics, connected 1/2/3-gram networks, dependency/morphology/cohesion tools, six frozen neural backbones, eight original discourse classifier heads, and a typed 43-object/66-incidence source candidate. Native Laya/Jev distributions condition Qwen in three layers. Each layer trains both tiny students for 250 updates before Qwen feedback and 250 after it: 1,500 updates per student. The students fork immutable philosophy checkpoints and fuse 3,903 continuous features with explicit missing-value masks.

The student outputs are the original 26 logic heads. Eighteen interpretation axes and eight specification heads are observer input features, not additional student output heads. Exact prompts, responses, failed attempts, logits, checkpoints, source spans, update events, and byte-verified ResearchGraph receipt are retained in the evidence directory. Successful trajectory calls: 18 Jev, 18 Laya, 18 Qwen initial, 18 Qwen feedback. Failed/interrupted attempts are retained separately and excluded from these accepted-call counts.

## Measured results and limits

On the single held-out paragraph, the symbolic student matches 22/26 Qwen pseudo-labels when conditioned, versus 20/26 with all observer features masked. The probabilistic student's MSE to Jev is 0.021893 conditioned versus 0.011719 masked: conditioning worsens this diagnostic. These are distillation measurements, not gold accuracy or truth calibration.

The 4/1/1 split is within one source document. Whole-source graph context is transductive; generalization to unseen sources is not established. Qwen still proposes unsupported proof-rule labels and invalid Boolean formulas. Source graphs and interpretations remain candidates; native semantic admission is NOT_RUN. Schema checks and source anchors do not prove semantic fidelity.

## Reproduction

This is a workstation pilot, not a portable package. Scripts currently resolve /home/user0/FIM/experiment and depend on the existing external corpusGraph semantic_tower inventories, frozen checkpoints/backbones, configured Qwen/Laya services, Jev client credentials, lexical environment, and RecursiveCAS ResearchGraph libraries. No credentials or heavyweight neural model weights are included. Evidence includes the two small trained bridge checkpoints; origin snapshots and large model weights are pinned and archived in local ResearchGraph.

Run bridge_features.py in the configured lexical/neural environments, then philosophy_spec_bridge.py with an initialized run directory. After completion, run verify_philosophy_spec_bridge.py, inspect_bridge_students.py, and register_philosophy_spec_bridge.py in the Torch environment. keyword_view.py rebuilds the existing network.html viewer with the latest report. Captured bridge-source.py and feature-source.py identify executed code; current script improvements and resumed attempts are explicitly recorded.

Validation: four pytest checks passed; standalone typed SHG adapter, text primitives, and extended metrics checks passed; bridge verifier confirms update ordering, immutable origin lineage, score/missing-value projection, eight actual classifier logits, exact source spans and checkpoint replay.
