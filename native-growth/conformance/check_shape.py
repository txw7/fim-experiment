#!/usr/bin/env python3
"""Fail closed on missing structured SHG families; no label inference."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def check(candidate):
    manifest = json.loads((ROOT / 'target-manifest.json').read_text())
    raw = (ROOT / 'target-index.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != manifest['target_sha256']:
        raise ValueError('frozen-target-digest-mismatch')
    required = set(manifest['family_counts'])
    members = candidate.get('members', [])
    present = Counter(m['kind'] for m in members if isinstance(m, dict) and 'kind' in m)
    missing = sorted(required - set(present))
    return {'schema': 'shg-shape-coverage-v1', 'target_digest': manifest['target_sha256'],
            'structured_family_counts': dict(sorted(present.items())),
            'missing_families': missing,
            'family_coverage': 'INCOMPLETE' if missing else 'PRESENT',
            'native_correspondence': 'NOT_CHECKED',
            'behavioral_proof': 'OPEN',
            'accepted_as_full_native_shg': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('candidate', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = check(json.loads(args.candidate.read_text()))
    text = json.dumps(report, indent=2) + '\n'
    if args.output:
        args.output.write_text(text)
    else:
        print(text, end='')
    raise SystemExit(1 if report['family_coverage'] == 'INCOMPLETE' else 0)
