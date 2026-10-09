"""Runnable adapter/role/binding/isolation checks, independent of training scores."""
import copy, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import torch
import unified_shg_student as s

def run():
    torch.set_num_threads(2); torch.manual_seed(137)
    run = Path((s.LIFT / 'latest.txt').read_text().strip())
    payload = json.loads((run / 'candidate.json').read_text())
    g = s.graph_input(payload)
    assert len(g['nodes']) == 88
    assert s.anchors(payload)['native_admission'] == 'NOT_RUN'
    r5, r4 = [g['native_ids'].index(k) for k in ('R5', 'R4')]
    assert any(e['relation'] == r5 and e['participant'] == r4 and e['role'] == 'inference-relation' for e in g['incidences'])
    altered = copy.deepcopy(payload)
    for o in altered['objects']:
        o['status'] = 'FAKE_ADMITTED'; o['identity'] = 'target-leak'
    altered['counterexample'] = {'target': 'changed'}
    assert s.graph_input(altered) == g, 'Verdicts/provenance must not enter model features'
    altered['objects'][0]['source']['quote'] = 'wrong'
    try: s.anchors(altered)
    except ValueError: pass
    else: raise AssertionError('Bad source anchor accepted')
    tokens = s.observation_tokens({'jev': {'answers': {'network_fit': {'choice': 'per_choice', 'probabilities': {'per_choice': 0.0}}}}})
    assert 'P:per_choice:0' in tokens and 'P:common_good:MISSING' in tokens
    assert 'CONF:MISSING' in tokens
    assert all(t in s.token_vocabulary() for t in tokens)
    try: s.observation_tokens({'jev': {'answers': {'network_fit': {'probabilities': {'per_choice': .8, 'common_good': .8}}}}})
    except ValueError: pass
    else: raise AssertionError('Invalid probability mass accepted')
    tower = s.load_tower(); data = s.dataset(tower)
    for shape, expected in [('per_choice', [1, 0]), ('common_witness', [0, 1]), ('captured_subject', [0, 0]), ('reversed_arguments', [0, 1])]:
        control = s.controls(tower, shape, 3, 0, 4, 71)
        distance, applications, _ = s.graph_axes(control)
        aims = next(i for i, n in enumerate(control['nodes']) if n['type'] == 'operator:AIMS' and control['native_ids'][i].startswith('N3/'))
        operands = {role: p for role, _, p in applications[aims]}
        assert [distance[operands[x]] for x in ('subject', 'object')] == expected
        assert all(t in s.token_vocabulary() for t in s.graph_tokens(control))
    bad_binding = copy.deepcopy(payload)
    binding = next(o for o in bad_binding['objects'] if o['id'].startswith('N3/') and o.get('family') == 'binding')
    next(e for e in binding['incidences'] if e['role'] == 'binder')['target'] = 'N1/formula/binder'
    try: s.graph_axes(s.graph_input(bad_binding))
    except ValueError: pass
    else: raise AssertionError('Cross-network binding capture accepted')
    groups = {k: {r['parent_group'] for r in rows} for k, rows in data.items()}
    assert not (groups['train'] & groups['validation'] or groups['train'] & groups['test'] or groups['validation'] & groups['test'])
    assert all(not (groups[a] & groups[b]) for a in groups for b in groups if a != b)
    hashes = [r['structure_hash'] for rows in data.values() for r in rows]
    assert len(hashes) == len(set(hashes))
    types = sorted({n['type'] for rows in data.values() for r in rows for n in r['graph']['nodes']} | {n['type'] for n in g['nodes']})
    roles = sorted({e['role'] for rows in data.values() for r in rows for e in r['graph']['incidences']} | {e['role'] for e in g['incidences']})
    model = s.Student(types, roles).eval()
    row = data['train'][0]
    reverse = copy.deepcopy(row); size = len(reverse['graph']['nodes'])
    reverse['graph']['nodes'].reverse(); reverse['graph']['native_ids'].reverse()
    for e in reverse['graph']['incidences']:
        e['relation'] = size - 1 - e['relation']; e['participant'] = size - 1 - e['participant']
    reverse['graph']['incidences'].reverse()
    with torch.no_grad():
        a = model([row])[0]; b = model([reverse])[0]
        assert torch.allclose(a, b, atol=1e-6), 'Local node permutation changed result'
        c = model([row, data['test'][0]])[0][0]
        assert torch.allclose(a[0], c, atol=1e-6), 'Batch graph crossed an example boundary'
        changed = copy.deepcopy(row)
        for e in changed['graph']['incidences']:
            if e['role'] == 'subject': e['role'] = 'object'
        assert not torch.allclose(a, model([changed])[0], atol=1e-6), 'Typed role changes disappeared'
        missing = copy.deepcopy(row); missing['observations'] = {}
        assert torch.allclose(model([row], observation_mask=True)[0], model([missing])[0])
    bad = copy.deepcopy(payload)
    next(o for o in bad['objects'] if o['kind'] == 'relation')['incidences'][0]['target'] = 'missing'
    try: s.graph_input(bad)
    except ValueError: pass
    else: raise AssertionError('Dangling reference accepted')
    obs = s.real_observations(run, 'per_choice')
    assert 'confidence' not in obs['qwen']['answers']['network_fit']
    assert 'probabilities' not in obs['qwen']['answers']['network_fit']
    print('PASS: native 88 objects; relation operands; anchors; no verdict leakage; zero/missing; mass validation; parent/structure splits; node permutation; role sensitivity; batch isolation; observer masking; dangling references; native Qwen missing scores')

if __name__ == '__main__': run()
