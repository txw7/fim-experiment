Tools obtained for the four-corpus symbolic/statistical stack

Runtime: working/text-tools-venv (isolated Python 3.12).
Python package versions: scripts/text-tools-requirements.lock.
Sources and downloaded archives: deps/text-tools.
Outputs: working/text-primitives. None of these acquisitions modifies the
Qwen/Laya servers or trains the classifier students.

Run:

    working/text-tools-venv/bin/python tests/test_extended_text_metrics.py
    working/text-tools-venv/bin/python scripts/extended_text_metrics.py
    working/text-tools-venv/bin/python scripts/text_tool_smoke.py

| Capability | Tool or implementation | Verified state |
| --- | --- | --- |
| Hypergeometric lexical specificity | SciPy hypergeom.logsf | Full four-corpus run; unadjusted random-token null |
| Entropy, conditional entropy, MI, concentration | Count formulas | Full run; adjacent pairs stay within source units |
| KL/JS comparison | Smoothed empirical distributions | Full run; alpha=.5 and compared vocabulary recorded |
| Cross-entropy, perplexity, token surprisal | Smoothed unigram with UNK | Hash-based held-out source units; count model, no neural LM |
| Dispersion | Family rates, entropy, DP | Full run; unequal corpus-family sizes accounted for |
| Skip-grams | Ordered pairs at distances 2 and 3 | Full run; count >=3; source boundaries retained |
| Text reuse | Shared cross-family exact trigrams | Full run; candidates, not evidence of historical influence |
| Variant clustering | RapidFuzz Damerau-Levenshtein | Same-prefix, length-near candidates; not exhaustive, no identity admission |
| Connectivity, path length, clustering, degree | NetworkX | Full graph; path mean from 64 fixed-seed origins in largest component |
| Small-world and power-law tests | NetworkX / powerlaw | Tool obtained; no guaranteed property or fitted status claimed |
| Graph kernels | GraKeL | Package obtained; separate from semantic entailment |
| Repetition and diversity | zlib, TTR/RTTR/CTTR, SacreBLEU | Full count profiles; Self-BLEU uses <=32 fixed-seed units per family |
| Vocabulary coverage | Empirical growth curve | Source order, no temporal or saturation claim |
| Stemming | Installed Snowball libstemmer | Full run |
| Morphological segmentation / MDL family | Morfessor Baseline | Full vocabulary segmented; stopped after 3 epochs under a 5-epoch ceiling |
| Keyword graph extraction | RaKUn 2 | Installed; one pinned source unit per family smoke run |
| Lemmas, dependency relations, dependency distance | spaCy en_core_web_sm 3.8.0 | Installed CPU model; four source-unit smoke runs |
| Cohesion, connectives, givenness | TAACO 2.1.3 | Official source downloaded; four-source smoke CSV verified |
| Polysemy, synonyms, pronunciation | WordNet, OMW, CMUdict | Official plaintext ZIP archives downloaded with hashes |
| Tokenizer resources | NLTK punkt_tab | Official data ZIP downloaded; no pickle data loaded |
| LDA/HDP and count-vector composition | Gensim / scikit-learn | Installed and imported; topic models not fitted |
| Co-occurrence / bibliometric R networks | cooccure / bibnets | Official source obtained; R runtime absent |
| Text alignment | TextPAIR | Source obtained; PostgreSQL/web deployment not performed |
| Historical text-reuse suite | TRACER | Published source host vcs.etrap.eu fails DNS; not obtained |
| English finite-state meter | ZeuScansion | Source obtained; foma/hunpos runtime absent |
| English poetic analysis | SPARSAR | Published Ubuntu download redirects to Google sign-in; binary not obtained |
| Scandroid | Published author download page | Returns HTTP 404; not obtained |
| Pronunciation/rhyme utilities | pronouncing | Package obtained; works on English pronunciations, not original Greek meter |
| Contextual lexical change / APD | XL-LEXEME | Official source obtained; 2.24 GB neural weights not downloaded |
| BERT keyword graphs | KinGBERT 0.0.2 | PyPI source archive obtained; neural dependencies/model not loaded |
| Constituency, Yngve, T-unit analysis | benepar | Package obtained; constituency model and operational definitions still required |
| AMR alignment | amrlib | Package obtained; AMR weights/alignment classifier not obtained |
| Grounding / relation-preservation framework | HalluGraph | Primary paper found; no public implementation identified in the checked paper |
| Sense distributions and time shifts | Annotation / dated source data | Requires sense/time annotations; present corpus families are not time slices |
| Qualia, inheritance, predicate/argument roles | Typed ontology / existing logical tower | Cannot derive licensed semantic roles from co-occurrence counts alone |
| Compound semantic overlap, Katz gamma, generic informativity | Definition-dependent | No unsupported formula introduced; exact definitions/reference needed |
| Human association norms, VAD, Hungarian rhyme rules | External data / language-specific rules | Not replaced by English counts; those data/rules are not yet obtained |

Acquisition receipt: working/text-primitives/tool-acquisition.json includes source
commits, installed versions, archive hashes and exact unresolved downloads.
Archive-only entries are not claimed installed or runnable.

Primary origins:

- SciPy: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.hypergeom.html
- Morfessor: https://github.com/aalto-speech/morfessor
- RaKUn: https://github.com/SkBlaz/rakun2
- TAACO: https://github.com/LCR-ADS-Lab/TAACO
- TextPAIR: https://github.com/ARTFL-Project/text-pair
- cooccure: https://github.com/mohsaqr/cooccure
- bibnets: https://github.com/mohsaqr/bibnets
- ZeuScansion: https://github.com/manexagirrezabal/zeuscansion
- XL-LEXEME: https://github.com/pierluigic/xl-lexeme
- KinGBERT: https://pypi.org/project/KinGBERT/
- NLTK data: https://github.com/nltk/nltk_data
- TRACER: https://tracer.gitbook.io/manual
- SPARSAR: https://sparsar.wordpress.com/sparsar/
- Scandroid: https://oak.conncoll.edu/cohar/Programs.htm
- HalluGraph: https://arxiv.org/html/2512.01659v1

Statistical significance, semantic interpretation, logical validity and structural
SHG declaration are distinct proof levels. Added Python artifacts do not upgrade
SHG execution bindings or proof obligations.
