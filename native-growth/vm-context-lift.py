"""Reuse the symbolic lifting calculus; no FIM or native graph admission."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys

OWNER = Path('/home/user0/semalg-flow-viewer/tower')
sys.path.insert(0, str(OWNER))
from calculus import atom, var, lam, call, apply, arrow, infer, free, normalize, pretty, digest, SIGNATURES, selfcheck
from analyze import graph_export

ROOT = Path(__file__).resolve().parent

def compose(first, second):
    a, b = infer(first), infer(second)
    if not isinstance(a, tuple) or not isinstance(b, tuple) or a[2] != b[1]:
        raise TypeError('Composition interface mismatch')
    x = var('input', a[1])
    return lam(x, apply(second, apply(first, x)))

def main(out):
    out.mkdir(parents=True, exist_ok=False)
    raw = (ROOT / 'evidence/joint-growth/view.json').read_bytes()
    view = json.loads(raw)
    headers = {h['scope']: h for h in view['headers']}
    bindings = {}
    def operation(name, before, after):
        matches = [n for n in view['nodes'] if n['scope'] == 'parent'
                   and n['registry'] == 'member-registry-v1' and n['label'] == ':' + name.upper()]
        if len(matches) != 1:
            raise ValueError('Missing or ambiguous source operation: ' + name)
        node = matches[0]
        bindings[name] = {'native_member': node['id'], 'native_address': node['address'],
                          'header': headers[node['scope']], 'interface': [before, after],
                          'interface_status': 'PROPOSED; native interface remains OPEN'}
        return atom(name, arrow(before, after), node['address'])

    fetch = operation('fetch', 'VmState', 'Fetched')
    decode = operation('decode', 'Fetched', 'Decoded')
    execute = operation('execute', 'Decoded', 'StepResult')
    # Authored decomposition law, not a hand-built incidence or route table.
    step_application = compose(compose(fetch, decode), execute)
    step, step_events = normalize(step_application)
    work = var('work', arrow('VmState', 'StepResult'))
    SIGNATURES['bounded-loop-region'] = (
        ('work', arrow('VmState', 'StepResult')), ('policy', 'LoopPolicy'),
        ('effects', 'EffectBoundary'), arrow('VmState', 'RunResult'))
    context = lam(work, call('bounded-loop-region', work,
        atom('budget/correlation/continue/exit obligations OPEN', 'LoopPolicy'),
        atom('vm-state-access; containment obligation OPEN', 'EffectBoundary')))
    # L accepts a generator, rather than a completed inner graph.
    f = var('generator', arrow('VmState', 'StepResult'))
    lifting = lam(f, apply(context, f))
    construction = apply(lifting, step)
    run, events = normalize(construction)
    assert not free(run)
    assert infer(run) == arrow('VmState', 'RunResult')
    assert normalize(run)[1] == []
    assert run.args[0] == step

    # Extract ordered CALL uses and value connections from nested applications.
    # Source term is the authority for this candidate projection. No native rows
    # are manufactured, and these addresses are term coordinates, not H002.
    uses, edges = [], []
    namespace = digest(step)
    def walk(t, path):
        if t.kind == 'var':
            return {'kind': 'boundary-input', 'address': namespace + '#input', 'type': t.type}
        if t.kind != 'apply' or t.args[0].kind != 'atom':
            raise ValueError('Unsupported candidate call form')
        function, argument = t.args
        incoming = walk(argument, path + '/argument')
        before, after = function.type[1:]
        assert incoming['type'] == before
        use = {'kind': 'CALL-use', 'address': namespace + '#' + path,
               'callee': function.name, 'callee_native_address': function.origin,
               'input_type': before, 'output_type': after}
        uses.append(use)
        edges.append({'kind': 'DATAFLOW', 'source': incoming['address'],
                      'target': use['address'], 'value_type': before,
                      'derivation': 'typed application argument -> function input'})
        return {'kind': 'call-result', 'address': use['address'], 'type': after}
    result = walk(step.args[0], 'step/body')
    edges.append({'kind': 'DATAFLOW', 'source': result['address'],
                  'target': namespace + '#result', 'value_type': result['type'],
                  'derivation': 'lambda body -> boundary result'})
    assert [u['callee'] for u in uses] == ['fetch', 'decode', 'execute']
    rejected = False
    try:
        compose(fetch, atom('wrong-decode', arrow('Other', 'Decoded')))
    except TypeError as error:
        assert str(error) == 'Composition interface mismatch'
        rejected = True
    assert rejected
    alternative = compose(fetch, atom('inspect-fetched', arrow('Fetched', 'StepResult')))
    assert infer(alternative) == infer(step) and digest(alternative) != digest(step)
    # Same enclosure accepts a different lawful generator without editing it.
    alternate_run, _ = normalize(apply(lifting, alternative))
    assert infer(alternate_run) == infer(run) and alternate_run != run
    receipt = {'schema': 'vm-context-lift-candidate-v1',
               'source_view_sha256': hashlib.sha256(raw).hexdigest(),
               'source_pins': {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in [OWNER / 'calculus.py', OWNER / 'analyze.py', Path(__file__)]},
               'bindings': bindings, 'decomposition_origin': 'authored sequence law',
               'loop_semantics': 'OPEN; retained policy, not an executing loop',
               'step_beta_events': step_events, 'enclosure_beta_events': events,
               'calculus_checks': selfcheck(), 'interface_mismatch_rejected': rejected,
               'alternative_generator_same_boundary': True,
               'calls': uses, 'dataflows': edges,
               'native_admission': False, 'effect_preservation': 'OPEN',
               'behavioral_proof': 'OPEN', 'model_calls': 0, 'fim_calls': 0}
    terms = {'context': context, 'lift': lifting, 'step-generator': step,
             'run-candidate': run, 'alternative-run': alternate_run}
    (out / 'terms.json').write_text(json.dumps({k: asdict(v) for k,v in terms.items()}, indent=2)+'\n')
    (out / 'graph.json').write_text(json.dumps(graph_export(run, digest(run)), indent=2)+'\n')
    (out / 'construction.lisp.txt').write_text('\n\n'.join(k+'\n'+pretty(v) for k,v in terms.items())+'\n')
    (out / 'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps({'calls': len(uses), 'dataflows': len(edges),
                      'interface_mismatch_rejected': rejected,
                      'alternative_generator_same_boundary': True,
                      'native_admission': False, 'fim_calls': 0}, indent=2))

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
