# S3 readable candidate normalizer

This small projection turns the bounded v17 S3 candidate graph into an
indented, human-readable view. It reconstructs the nested topology from the
graph's ordered child incidences, verifies the reconstructed tree against the
source expression, preserves the model's five unresolved cross-link results,
and retains all eleven open feedback slots. Exact source text and offsets are
written to `provenance.txt`.

Run the checked example:

```sh
python s3-normalization-v1/normalize_s3_candidate.py \
  --run s3-normalization-v1/example/input \
  --out /tmp/s3-normalized
python -m unittest discover -s s3-normalization-v1/tests -p 'test_*.py'
```

The output is a readable candidate projection. It is 13% smaller than the raw
S3 source by bytes, but this is not a semantic compression or equivalence
proof. No semantic rewrite law is applied; native admission and live provider
execution remain unrun. The source graph and Qwen request/response are kept in
`example/input/`, and the generated output is shown under `example/output/`.
