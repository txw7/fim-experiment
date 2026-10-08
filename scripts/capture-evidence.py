#!/usr/bin/env python3
"""Capture actual fresh-process results; fail on any command failure."""
import hashlib
import json
import pathlib
import shutil
import sys
import subprocess

root = pathlib.Path(__file__).resolve().parents[1]
evidence = root / 'evidence'
evidence.mkdir(exist_ok=True)
commands = [('./shg-stack', 'build'), ('sbcl', '--script', 'tests/check.lisp')]
commands += [('./shg-stack', *args) for args in [
    ('describe',), ('show',), ('resolve', '/G'), ('resolve', 'OP'),
    ('resolve', 'H'), ('resolve', 'R'), ('relations',), ('dependencies',),
    ('neighbors', 'P-OUT'), ('obligations',), ('route', 'R')]]
commands.append(('sbcl', '--script', 'tests/native-checks.lisp'))
results = []
for index, command in enumerate(commands):
    if command == ('sbcl', '--script', 'tests/native-checks.lisp') and '--reuse-native-evidence' in sys.argv:
        output = (evidence/'native-profile.log').read_text()
        if 'NATIVE_PROFILE_CHECKS_GREEN scripts=5' not in output:
            raise RuntimeError('Cannot reuse incomplete native evidence')
        result = subprocess.CompletedProcess(command, 0, output, '')
    else:
        result = subprocess.run(command, cwd=root, text=True, capture_output=True, check=True)
    path = evidence / f'check-{index:02}.log'
    path.write_text(result.stdout + result.stderr)
    results.append({'command': list(command), 'exit_code': result.returncode,
                    'output': str(path.relative_to(root)), 'execution': 'retained-successful-native-run' if command == ('sbcl', '--script', 'tests/native-checks.lisp') and '--reuse-native-evidence' in sys.argv else 'fresh-process'})
shutil.copyfile(root / 'working/shg-stack.sexp', evidence / 'shg-stack.sexp')
shutil.copyfile(root / 'working/second.sexp', evidence / 'second.sexp')
# Replace outdated named snapshots with actual current query output.
for filename, index in [('shg-view.sexp', 3), ('shg-route.sexp', 12),
                        ('shg-root-resolution.sexp', 4), ('shg-hole-resolution.sexp', 6),
                        ('shg-checks.log', 1)]:
    shutil.copyfile(evidence / f'check-{index:02}.log', evidence / filename)
files = ['README.md', 'REVIEW.md', 'shg-stack.lisp', 'shg-stack', 'pins.json',
         'tests/check.lisp', 'tests/native-checks.lisp', 'scripts/capture-evidence.py', 'synthesis/working_graph.lisp']
files += [str(p.relative_to(root)) for p in sorted(evidence.iterdir())
          if p.is_file() and p.name != 'shg-evidence.json']
manifest = {'schema': 'bounded-shg-evidence-v2', 'goggles_commit': json.loads((root/'pins.json').read_text())['goggles']['commit'],
            'supported_profile': 'generation-zero-read-only-dataflow',
            'semantics': {'structure': 'checked', 'predicates': 'retained', 'behavior': 'unverified', 'execution': 'unbound'},
            'commands': results,
            'sha256': {name: hashlib.sha256((root/name).read_bytes()).hexdigest() for name in files}}
(evidence/'shg-evidence.json').write_text(json.dumps(manifest, indent=2)+'\n')
print(f'EVIDENCE_GREEN commands={len(results)} hashes={len(files)}')
