Run from FIM/experiment:

    python tests/test_text_primitives.py
    python scripts/text_primitives.py
    python scripts/keyword_view.py
    SHG_GOGGLES_ROOT="$PWD/deps/literate-goggles" sbcl --script scripts/text_primitives_shg.lisp

The four inputs are pinned by file hash and source-unit references in sources.jsonl.
Artifacts are generated under ignored working/text-primitives. No model call is
needed for the lexical observations. Snowball uses the installed libstemmer.

Association events are ordered token endpoints of within-document windows. Each
observed forward pair contributes both directions. This shared event population
supports PMI, PPMI, NPMI, lift, conditional confidence, conviction, logDice and
2x2 log-likelihood statistics. Overlapping windows violate an independent-trial
assumption: LLR is an association statistic here, not a calibrated significance
or semantic-relation test. No p-values or universal significance cutoff are
reported. Undefined NPMI or conviction is null, never silently zero.

Term dispersion uses four corpus-family buckets; their unequal sizes are exposed
through per-family rates. Spacing gaps never cross source units. Compression
uses zlib bytes and includes framing overhead, so short units can exceed ratio 1.
RTTR/CTTR remain length-sensitive; none is a calibrated semantic-density score.
The graph excludes self-loops and retains pairs of count >=3. PageRank uses
weighted edges, damping .85, and 30 iterations. Display geometry is a spiral,
not an embedding or inferred semantic distance. The viewer shows 70 nodes;
the full network is retained in keyword-network.json.

Logical words are retained. Stem variants stay separate from surface terms.
Neither lemmatization, logical parsing, semantic identity, entailment, small-world
status, nor a power-law fit is claimed. Aristotle source units include editorial
material; Parmenides contains translation alternatives. These inputs are pinned,
not certified pristine.

SHG declaration uses the repository's native nominal artifact-reference type,
operation addresses and dataflow routes. Execution bindings remain UNBOUND and
obligations UNKNOWN. Numeric artifacts are produced by Python; the structural
SHG graph does not execute the pipeline or certify those results.
