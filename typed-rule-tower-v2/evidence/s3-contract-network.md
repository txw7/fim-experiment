# S3 contract candidate network

- [Open the interactive network](s3-contract-network.html)
- [Inspect the expanded graph data](s3-contract-network.json)
- [Inspect the model prompt trace](s3-contract-prompt-trace.json)

The page renders the source-anchored candidate graph as a radial, multi-level
web with typed relation incidences, selectable objects, composition depth,
open construction goals, and any saved observer probabilities. The displayed
selection contains 24 objects/networks, 11 relation instances, and 39 visible
incidences; these are view counts, not admission or correctness metrics.

There is no prompt output for this graph. It was constructed by deterministic
source extraction, and its saved observer set is empty. The viewer and trace
file say so explicitly; neither supplies synthetic Jev, Laya, or Qwen answers.
To publish real prompt/output records, a prompted run must first save the exact
request and response with provenance, then regenerate the graph bundle.

The graph is marked `INCOMPLETE_CANDIDATE`; native semantic admission is
`NOT_RUN`. The HTML is a self-contained inspection artifact. It does not
perform provider calls or write to ResearchGraph.
