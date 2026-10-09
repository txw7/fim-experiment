# Fresh S3 tower

Run with the existing Torch environment:

```bash
/home/user0/.local/share/aristotle-observer-venv/bin/python scripts/fresh_s3_tower.py
/home/user0/.local/share/aristotle-observer-venv/bin/python scripts/verify_fresh_s3.py
python scripts/register_fresh_s3.py
python scripts/keyword_view.py
```

Each invocation creates a separate timestamped directory and a newly initialized tiny model. It reads the source spec as data and makes new Qwen, Laya and Jev classification requests. It never executes the spec's provider instructions. Qwen's structural proposals are checked for exact quote grounding, unique IDs, valid references and acyclic relation composition. Up to two additional fresh correction requests retain rejected proposals and validation errors.

There are four training paragraphs, one validation paragraph and one test paragraph from the same S3 document. Each training paragraph causes 250 optimizer updates before a new Qwen feedback call and 250 after it. Replay replaces the prior version of that paragraph, rather than counting feedback as another independent example. The live model continues updating; the incumbent is promoted only by validation log loss. Test paragraphs never enter replay or promotion.

Four heads predict dominant obligation mode, relation type, composition and concept kind. The input combines source tokens, discrete observer fields with missing values and a bottom-up encoding of typed concept/relation incidences. Relations may consume earlier relations. These extracted graphs remain candidates; schema checks and training do not establish native SHG admission or source interpretation correctness.

Qwen feedback supplies pseudo-labels. Combined-input agreement includes those teacher labels as input and measures aggregation plumbing, not independent classification accuracy. The source-only ablation masks both observer and graph features. One held-out paragraph cannot establish corpus generalization or calibration. This run trains the new tiny student, not Qwen, Laya or Jev.

`events.jsonl` records actual call/update order. Initial, live and incumbent checkpoints, immutable runner/source snapshots, requests, responses, logits, repair errors and checkpoint replay checks are retained. The existing ResearchGraph receives a separate experiment and checkpoint artifacts; earlier experiments remain intact. The same network viewer presents the fresh run above historical experiments.

The measured run can resume its own live checkpoint after extraction failure; the resume event explicitly records an optimizer reset. It does not load a prior experiment's checkpoint. Operator outputs are normalized as sets with the raw response retained.
