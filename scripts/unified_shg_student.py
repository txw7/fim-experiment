"""CPU pilot: native SHG incidences + typed observer slots -> tiny transformer.

Generated controls test the plumbing. The single authored SHG fixture is a
separate probe; neither a model score nor an exact source anchor admits a graph.
"""
import argparse, collections, copy, hashlib, importlib.util, itertools, json, random, time
from pathlib import Path
import torch
from torch import nn

ROOT = Path(__file__).resolve().parents[1]
LIFT = Path('/home/user0/semalg-flow-viewer/shg-lift')
CHOICES = ['supported', 'unsupported', 'unresolved']
READINGS = ['per_choice', 'common_good', 'neither', 'unresolved']
SHAPES = ['per_choice', 'common_witness', 'captured_subject', 'reversed_arguments']
OBSERVERS = ['jev', 'laya', 'qwen', 'qwen-feedback']

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')

def load_tower(path=None):
    spec = importlib.util.spec_from_file_location('authored_shg_fixture', path or LIFT / 'tower.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def graph_input(payload):
    """Whitelist carrier fields. Status, hashes, obligations and verdicts stay out."""
    objects = payload['objects']
    ids = [o['id'] for o in objects]
    if len(ids) != len(set(ids)) or not ids or len(ids) > 512:
        raise ValueError('Invalid object identities/count')
    index = {key: i for i, key in enumerate(ids)}
    query = next((o.get('interior_root') for o in objects if o['id'] == 'N3'), None)
    if query is None:
        raise ValueError('N3 must expose an interior root')
    nodes, edges = [], []
    for i, o in enumerate(objects):
        subtype = o.get('operator', o.get('family', o.get('network_type', '')))
        nodes.append({'type': o['kind'] + ':' + subtype,
                      'value_type': o.get('value_type', o.get('variable_type', 'none')),
                      'query_target': o['id'] == query})
        incidences = list(o.get('incidences', []))
        for key in ('owner', 'interior_root'):
            if key in o:
                incidences.append({'target': o[key], 'role': 'metadata:' + key, 'position': 0})
        incidences += [{'target': x, 'role': 'metadata:interior_member', 'position': j}
                       for j, x in enumerate(o.get('interior_members', []))]
        slots = set()
        for e in incidences:
            slot = (e['role'], e['position'])
            if e['target'] not in index or slot in slots or not isinstance(e['position'], int) or not 0 <= e['position'] < 256:
                raise ValueError('Dangling, duplicate or invalid incidence')
            slots.add(slot)
            edges.append({'relation': i, 'participant': index[e['target']],
                          'role': e['role'], 'position': e['position']})
    if sum(n['query_target'] for n in nodes) != 1:
        raise ValueError('Expected one exposed formula-root query target')
    return {'nodes': nodes, 'incidences': edges, 'native_ids': ids, 'query_native_id': query}

def anchors(payload):
    if digest(payload['source']) != payload['source_digest']:
        raise ValueError('Source digest mismatch')
    checked = 0
    for o in payload['objects']:
        a = o.get('source')
        if a:
            if payload['source'][a['unit']][a['char_start']:a['char_end']] != a['quote']:
                raise ValueError('Source span mismatch: ' + o['id'])
            checked += 1
    return {'exact_anchors': checked, 'source_digest': payload['source_digest'],
            'interpretation': 'authored fixture; exact anchors do not establish semantic fidelity',
            'native_admission': payload.get('native_admission', 'NOT_RUN')}

def graph_axes(g):
    """Scope-relative bindings and bottom-up order, derived solely from incidences."""
    ports = collections.defaultdict(list)
    for e in g['incidences']:
        ports[e['relation']].append((e['role'], e['position'], e['participant']))
    applications, bindings, roots = {}, {}, []
    for i, node in enumerate(g['nodes']):
        if node['type'].startswith('relation:application-'):
            result = [p for role, _, p in ports[i] if role == 'result']
            if len(result) != 1 or result[0] in applications:
                raise ValueError('Ambiguous application result')
            applications[result[0]] = [(role, pos, p) for role, pos, p in ports[i] if role != 'result']
        elif node['type'] == 'relation:binding':
            d = {role: p for role, _, p in ports[i]}
            if set(d) != {'binder', 'use'} or d['use'] in bindings:
                raise ValueError('Ambiguous binder/use link')
            bindings[d['use']] = d['binder']
        elif node['type'].startswith('network:'):
            roots += [p for role, _, p in ports[i] if role == 'metadata:interior_root']
    distance = [16] * len(g['nodes'])  # Dedicated absent marker, not zero.
    def scope(n, env, path):
        if n in path:
            raise ValueError('Cyclic formula application; use bounded graph scoring separately')
        if g['nodes'][n]['type'] == 'variable-use:':
            binder = bindings.get(n)
            if binder not in env:
                raise ValueError('Variable binding lies outside lexical scope')
            d = list(reversed(env)).index(binder)
            if d >= 16: raise ValueError('Binding depth exceeds pilot budget')
            if distance[n] not in (16, d): raise ValueError('Ambiguous lexical binding context')
            distance[n] = d
        operands = applications.get(n, [])
        if g['nodes'][n]['type'] in ('operator:FORALL', 'operator:EXISTS'):
            p = {role: child for role, _, child in operands}
            if set(p) != {'variable', 'body'}: raise ValueError('Missing quantifier binder/body')
            scope(p['body'], env + [p['variable']], path | {n})
        else:
            for _, _, child in operands: scope(child, env, path | {n})
    for root in roots: scope(root, [], set())
    levels = {}
    def level(n, path):
        if n in path: raise ValueError('Cyclic application')
        if n not in levels:
            levels[n] = 1 + max([level(p, path | {n}) for _, _, p in applications.get(n, [])] or [-1])
        return levels[n]
    for n in applications: level(n, set())
    return distance, applications, levels

def graph_tokens(g):
    """Typed binding slots in query-subgraph order; names and verdicts excluded."""
    distance, applications, _ = graph_axes(g)
    bindings = {}
    for i, n in enumerate(g['nodes']):
        if n['type'] == 'relation:binding':
            ports = {e['role']: e['participant'] for e in g['incidences'] if e['relation'] == i}
            bindings[ports['use']] = ports['binder']
    binder_kinds = {child: g['nodes'][parent]['type'].removeprefix('operator:')
        for parent, ports in applications.items() for role, _, child in ports
        if role == 'variable' and g['nodes'][parent]['type'] in ('operator:FORALL', 'operator:EXISTS')}
    tokens = ['GRAPH_BINDINGS']
    def walk(parent):
        for role, pos, child in sorted(applications.get(parent, []), key=lambda e: (e[1], e[0])):
            if child in bindings:
                tokens.extend(['GRAPH_OP:' + g['nodes'][parent]['type'].removeprefix('operator:'),
                    'GRAPH_ROLE:' + role, 'GRAPH_POS:' + str(pos),
                    'BINDER_KIND:' + binder_kinds[bindings[child]], 'BINDER_DISTANCE:' + str(distance[child]), 'END_BINDING'])
            walk(child)
    walk(next(i for i, n in enumerate(g['nodes']) if n['query_target']))
    return tokens + ['END_GRAPH_BINDINGS']

def bin_value(value):
    if value is None:
        return 'MISSING'
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not 0 <= value <= 1:
        raise ValueError('Probability/confidence outside [0,1]')
    return str(min(10, int(value * 10 + .5)))

def observation_tokens(observations):
    tokens = ['OBS_SEQ']
    for observer in OBSERVERS:
        observation = observations.get(observer, {})
        tokens.append('OBS:' + observer)
        for head, options in [('network_fit', READINGS), ('support', CHOICES)]:
            answer = observation.get('answers', {}).get(head, {})
            choice = answer.get('choice')
            if choice is not None and choice not in options:
                raise ValueError('Unknown choice in ' + head)
            probabilities = answer.get('probabilities') or {}
            if set(probabilities) - set(options):
                raise ValueError('Unknown probability slot')
            present = [x for x in probabilities.values() if x is not None]
            if present and sum(present) > 1.0001:
                raise ValueError('Probability mass exceeds one')
            tokens += ['HEAD:' + head, 'CHOICE:' + (choice or 'MISSING'),
                       'CONF:' + bin_value(answer.get('confidence'))]
            tokens += ['P:' + c + ':' + bin_value(probabilities.get(c)) for c in options]
            tokens.append('END_HEAD')
        tokens.append('END_OBS')
    return tokens + ['END_OBS_SEQ']

def token_vocabulary():
    tokens = ['PAD', 'CLS', 'OBS_SEQ', 'END_OBS_SEQ', 'END_OBS', 'END_HEAD']
    tokens += ['OBS:' + x for x in OBSERVERS] + ['HEAD:network_fit', 'HEAD:support']
    tokens += ['CHOICE:' + x for x in READINGS + CHOICES + ['MISSING']]
    bins = [str(x) for x in range(11)] + ['MISSING']
    tokens += ['CONF:' + x for x in bins]
    tokens += ['P:' + c + ':' + b for c in READINGS + CHOICES for b in bins]
    tokens += ['GRAPH_BINDINGS', 'END_GRAPH_BINDINGS', 'END_BINDING']
    tokens += ['GRAPH_OP:' + x for x in ['FORALL', 'EXISTS', 'IF', 'AND', 'NOT', 'CHOICE', 'DELIBERATE-CHOICE', 'GOOD', 'AIMS']]
    tokens += ['GRAPH_ROLE:' + x for x in ['variable', 'body', 'condition', 'consequent', 'left', 'right', 'argument', 'subject', 'object']]
    tokens += ['GRAPH_POS:' + str(x) for x in range(16)]
    tokens += ['BINDER_KIND:FORALL', 'BINDER_KIND:EXISTS'] + ['BINDER_DISTANCE:' + str(x) for x in range(16)]
    return {x: i for i, x in enumerate(dict.fromkeys(tokens))}

def real_observations(run, candidate):
    observations = {}
    for observer in OBSERVERS:
        filename = run / 'observations' / (observer + '-response.json')
        response = json.loads(filename.read_text())
        if observer.startswith('qwen'):
            answer = json.loads(response['choices'][0]['message']['content'])
            answer = {'choice': answer['choice']}  # No invented Qwen confidence/probability.
        else:
            if response.get('usage', {}).get('truncated') or response.get('usage', {}).get('state_tokens_dropped'):
                raise ValueError('Truncated observer input')
            answer = response['answers']['network_fit']
        p = answer.get('probabilities')
        derived = {'choice': 'unresolved' if answer['choice'] == 'unresolved' else
                   'supported' if answer['choice'] == candidate else 'unsupported',
                   'confidence': answer.get('confidence')}
        if p:
            derived['probabilities'] = {'supported': p.get(candidate),
                'unsupported': sum(v for k, v in p.items() if k not in (candidate, 'unresolved')),
                'unresolved': p.get('unresolved')}
        observations[observer] = {'answers': {'network_fit': answer, 'support': derived},
            'reported_model': response.get('model'), 'family': 'qwen' if observer.startswith('qwen') else observer,
            'support_projection': 'candidate-relative marginal; not a calibrated verdict',
            'raw_response_sha256': hashlib.sha256(filename.read_bytes()).hexdigest()}
    return observations

def controls(tower, shape, depth, repeats, lift, seed):
    class ControlTower(tower.Tower):
        def add(self, key, kind, **fields):
            if key in self.objects or len(self.objects) >= 512:
                raise ValueError('Control object budget/identity error')
            self.objects[key] = {'id': key, 'kind': kind, **fields}
            return key
    t = ControlTower()
    x, y = 'w' + str(seed), 'u' + str(seed)
    conclusion = tower.quantified('DELIBERATE-CHOICE', x, y)
    if shape == 'common_witness':
        conclusion = ['EXISTS', y, ['AND', ['GOOD', y], ['FORALL', x, ['IF', ['DELIBERATE-CHOICE', x], ['AIMS', x, y]]]]]
    elif shape == 'captured_subject':
        conclusion = ['FORALL', x, ['IF', ['DELIBERATE-CHOICE', x], ['EXISTS', x, ['AND', ['GOOD', x], ['AIMS', x, x]]]]]
    elif shape == 'reversed_arguments':
        conclusion[2][2][2][2] = ['AIMS', y, x]
    # Idempotent conjunction and unused universal binders preserve truth conditions.
    def repeat_good(form):
        if form[0] == 'GOOD':
            result = form
            for _ in range(repeats):
                result = ['AND', copy.deepcopy(form), result]
            return result
        return [form[0], *[repeat_good(x) if isinstance(x, list) else x for x in form[1:]]]
    conclusion = repeat_good(conclusion)
    for i in range(depth):
        conclusion = ['FORALL', 'unused' + str(i), conclusion]
    model = {'domain': ['a', 'b', 'g0', 'g1'], 'predicates': {'CHOICE': {('a',), ('b',)},
        'DELIBERATE-CHOICE': {('a',), ('b',)}, 'GOOD': {('g0',), ('g1',)}, 'AIMS': {('a', 'g0'), ('b', 'g1')}}}
    assert all(tower.evaluate(f, model) for f in tower.FORMULAS[:2])
    assert tower.evaluate(conclusion, model) == (shape == 'per_choice')
    for i, formula in enumerate([*tower.FORMULAS[:2], conclusion], 1):
        n = 'N' + str(i)
        root = t.construct_formula(formula, 's' + str(i), n + '/formula')
        t.add(n, 'network', network_type='PropositionNetwork', interior_root=root)
        t.add(n + '/claim', 'port', owner=n, value_type='Proposition')
        t.relation(n + '/boundary', 'boundary', [('network', n), ('interior', root), ('export', n + '/claim')])
    t.add('N4', 'network', network_type='InferenceNetwork', interior_members=['R4'])
    t.relation('R4', 'inference', [('premise', 'N1/claim'), ('premise', 'N2/claim'),
        ('conclusion', 'N3/claim'), ('proof-network', 'N4')])
    t.add('N4/arbitrary', 'proof-parameter', value_type='Individual')
    for n in ('N1', 'N2', 'N3'):
        t.relation('N4/map/' + n, 'proof-substitution', [('source-binder', n + '/formula/binder'), ('proof-parameter', 'N4/arbitrary')])
    for n in ('N1', 'N2', 'N3', 'N4'):
        members = [x for x in t.objects if x.startswith(n + '/formula')] if n != 'N4' else ['R4', 'N4/arbitrary', *['N4/map/N' + str(i) for i in range(1, 4)]]
        t.relation(n + '/interior', 'containment', [('container', n), *[('member', x) for x in members]])
    parent, relation = 'N4', 'R4'
    for i in range(lift):
        n, r = 'N' + str(5 + i), 'R' + str(5 + i)
        t.add(n, 'network', network_type='DiscourseJustificationNetwork', interior_members=[r])
        t.relation(r, 'justification', [('argument-network', parent), ('supported-claim', 'N3/claim'), ('inference-relation', relation)])
        t.relation(n + '/interior', 'containment', [('container', n), ('member', r)])
        parent, relation = n, r
    graph = graph_input({'objects': list(t.objects.values())})
    return graph

def simulated_observations(label, seed):
    rng = random.Random(seed)
    if rng.random() < .25:
        return {}
    observations = {}
    correlated_error = rng.random() < .2
    for observer in OBSERVERS:
        if rng.random() < .2:
            continue
        error = correlated_error if observer.startswith('qwen') else rng.random() < (.12 if observer == 'jev' else .3)
        choice = 'supported' if bool(label) != error else 'unsupported'
        answer = {'choice': choice}
        if not observer.startswith('qwen'):
            p = rng.uniform(.55, .97)
            answer.update(confidence=p, probabilities={choice: p,
                ('unsupported' if choice == 'supported' else 'supported'): 1 - p, 'unresolved': 0.})
        observations[observer] = {'answers': {'support': answer}, 'authority': 'SIMULATED structural control; not a Jev/Laya/Qwen call'}
    return observations

def dataset(tower):
    result = {'train': [], 'validation': [], 'development': [], 'test': []}
    seen = set()
    configs = list(itertools.product(range(3), range(3), range(1, 4)))
    for d, r, l in configs + list(itertools.product((3, 4), range(3), (4, 5))) + list(itertools.product((5, 6), range(3), (6, 7))):
        if (d, r, l) == (0, 0, 1):  # Keep the original fixture shape out of training.
            continue
        group = f'generated-parent:{d}:{r}:{l}'
        split = 'test' if d >= 5 else 'development' if d >= 3 else 'validation' if int(digest(group)[:8], 16) % 5 == 0 else 'train'
        for shape in SHAPES:
            seed = int(digest([group, shape])[:8], 16)
            graph = controls(tower, shape, d, r, l, seed)
            key = digest({'nodes': graph['nodes'], 'incidences': graph['incidences']})
            if key in seen:
                raise ValueError('Duplicate structural control across splits')
            seen.add(key)
            label = int(shape == 'per_choice')
            result[split].append({'id': group + ':' + shape, 'parent_group': group, 'split': split,
                'graph': graph, 'observations': simulated_observations(label, seed), 'label': label,
                'shape': SHAPES.index(shape), 'structure_hash': key, 'authority': 'generated fixture transformation + evaluated countermodel; bounded authored support schema'})
    return result

class Student(nn.Module):
    def __init__(self, node_types, roles, width=16):
        super().__init__()
        self.node_vocab = {x: i for i, x in enumerate(node_types)}
        self.role_vocab = {x: i for i, x in enumerate(roles)}
        self.obs_vocab = token_vocabulary()
        self.types = nn.Embedding(len(node_types), width)
        self.value_vocab = {x: i for i, x in enumerate(['none', 'Individual', 'Proposition', 'ProofCandidate', 'JustificationCandidate'])}
        self.value_types = nn.Embedding(len(self.value_vocab), width)
        self.binding_depth = nn.Embedding(17, width)
        self.role = nn.Embedding(len(roles), width)
        self.position = nn.Embedding(256, width)
        self.up = nn.Linear(3 * width, width)
        self.down = nn.Linear(3 * width, width)
        self.update = nn.GRUCell(width, width)
        self.tokens = nn.Embedding(len(self.obs_vocab), width, padding_idx=0)
        self.obs_position = nn.Embedding(128, width)
        self.graph_slots = nn.Parameter(torch.randn(2, width) * .02)
        self.encoder = nn.TransformerEncoder(nn.TransformerEncoderLayer(width, 2, 2 * width,
            dropout=0, batch_first=True), 1, enable_nested_tensor=False)
        self.support = nn.Linear(width, 2)
        self.shape = nn.Linear(width, len(SHAPES))

    def forward(self, rows, graph_mask=False, observation_mask=False):
        offset = 0
        types, values, binding_depths, relations, participants, roles, positions, groups, targets = [], [], [], [], [], [], [], [], []
        applications = collections.defaultdict(list)
        sequences = []
        for i, row in enumerate(rows):
            g = row['graph']
            types += [self.node_vocab[n['type']] for n in g['nodes']]
            values += [self.value_vocab[n['value_type']] for n in g['nodes']]
            distance, app, levels = graph_axes(g)
            binding_depths += distance
            for parent, children in app.items():
                applications[levels[parent]].append((offset + parent,
                    [(role, pos, offset + p) for role, pos, p in children]))
            groups += [i] * len(g['nodes'])
            targets += [n['query_target'] for n in g['nodes']]
            for e in g['incidences']:
                relations.append(offset + e['relation']); participants.append(offset + e['participant'])
                roles.append(self.role_vocab[e['role']]); positions.append(e['position'])
            offset += len(g['nodes'])
            sequences.append([self.obs_vocab[x] for x in
                ([] if graph_mask else graph_tokens(g)) + observation_tokens({} if observation_mask else row['observations'])])
        r, p, group = [torch.tensor(x, dtype=torch.long) for x in (relations, participants, groups)]
        h = self.types(torch.tensor(types)) + self.value_types(torch.tensor(values)) + self.binding_depth(torch.tensor(binding_depths))
        role = self.role(torch.tensor(roles)) + self.position(torch.tensor(positions))
        degree = torch.bincount(torch.cat([r, p]), minlength=len(h)).clamp_min(1).unsqueeze(1)
        for _ in range(4):
            messages = torch.zeros_like(h)
            messages.index_add_(0, r, torch.tanh(self.up(torch.cat([h[p], h[r], role], -1))))
            messages.index_add_(0, p, torch.tanh(self.down(torch.cat([h[r], h[p], role], -1))))
            h = self.update(messages / degree, h)
        # Encode children first; a deeper parent uses the already encoded children.
        # Formula DAG order comes from typed applications, never slash-path spelling.
        for level in sorted(applications):
            parents, operand_parents, children, edge_roles, edge_positions = [], [], [], [], []
            for i, (parent, operands) in enumerate(applications[level]):
                parents.append(parent)
                for role, pos, child in operands:
                    operand_parents.append(i); children.append(child)
                    edge_roles.append(self.role_vocab[role]); edge_positions.append(pos)
            par = torch.tensor(parents); op = torch.tensor(operand_parents)
            edge = self.role(torch.tensor(edge_roles)) + self.position(torch.tensor(edge_positions))
            messages = torch.tanh(self.up(torch.cat([h[torch.tensor(children)], h[par[op]], edge], -1)))
            incoming = torch.zeros(len(par), h.shape[1]); incoming.index_add_(0, op, messages)
            incoming /= torch.bincount(op).unsqueeze(1)
            updated = h.clone(); updated[par] = self.update(incoming, h[par]); h = updated
        mean = torch.zeros(len(rows), h.shape[1]); mean.index_add_(0, group, h)
        mean /= torch.bincount(group).unsqueeze(1)
        target = h[torch.tensor(targets, dtype=torch.bool)]
        graph_vectors = torch.stack([mean, target], 1)
        if graph_mask:
            graph_vectors = torch.zeros_like(graph_vectors)
        graph_vectors = graph_vectors + self.graph_slots
        n = max(map(len, sequences))
        if n + 1 > 128:
            raise ValueError('Observation length exceeds model budget; no silent truncation')
        ids = torch.tensor([[self.obs_vocab['CLS'], *s, *([0] * (n - len(s)))] for s in sequences])
        text = self.tokens(ids) + self.obs_position(torch.arange(ids.shape[1]))
        sequence = torch.cat([text[:, :1], graph_vectors, text[:, 1:]], 1)
        mask = torch.cat([ids[:, :1] == 0, torch.zeros(len(rows), 2, dtype=torch.bool), ids[:, 1:] == 0], 1)
        encoded = self.encoder(sequence, src_key_padding_mask=mask)[:, 0]
        return self.support(encoded), self.shape(encoded)

def evaluate(model, rows, **masks):
    model.eval()
    logits, shape = [], []
    with torch.no_grad():
        for start in range(0, len(rows), 16):
            a, b = model(rows[start:start + 16], **masks)
            logits.extend(a.tolist()); shape.extend(b.argmax(-1).tolist())
    probs = torch.tensor(logits).softmax(-1)[:, 1]
    truth = torch.tensor([r['label'] for r in rows]); pred = probs >= .5
    f1 = []
    for value in (0, 1):
        tp = ((pred == value) & (truth == value)).sum(); fp = ((pred == value) & (truth != value)).sum(); fn = ((pred != value) & (truth == value)).sum()
        f1.append(float(2 * tp / (2 * tp + fp + fn).clamp_min(1)))
    predictions = [{'id': r['id'], 'target': int(y), 'prediction': int(p), 'support_probability': float(prob),
        'raw_logits': ls, 'shape_target': SHAPES[r['shape']], 'shape_prediction': SHAPES[s], 'parent_group': r['parent_group']}
        for r, y, p, prob, ls, s in zip(rows, truth, pred, probs, logits, shape)]
    return {'n': len(rows), 'accuracy': float((pred == truth).float().mean()), 'macro_f1': sum(f1) / 2,
        'brier': float((probs - truth).square().mean()), 'logloss': float(nn.functional.cross_entropy(torch.tensor(logits), truth)),
        'shape_accuracy': sum(s == r['shape'] for r, s in zip(rows, shape)) / len(rows), 'predictions': predictions}

def predict(input_path, checkpoint_path):
    checkpoint = torch.load(checkpoint_path, map_location='cpu', weights_only=True)
    config = checkpoint['config']; model = Student(config['types'], config['roles'], config['width']).eval()
    if model.obs_vocab != config['observation_vocabulary']:
        raise ValueError('Observation vocabulary/checkpoint mismatch')
    model.load_state_dict(checkpoint['state_dict'])
    packet = json.loads(Path(input_path).read_text())
    graph = packet.get('graph') or graph_input(packet)
    observation = packet.get('observations', {})
    with torch.no_grad():
        logits, shape = model([{'graph': graph, 'observations': observation}])
    types = collections.Counter(n['type'] for n in graph['nodes'])
    return {'raw_support_logits': logits[0].tolist(), 'support_probabilities': dict(zip(['unsupported', 'supported'], logits[0].softmax(-1).tolist())),
        'raw_composition_logits': shape[0].tolist(), 'composition_probabilities': dict(zip(SHAPES, shape[0].softmax(-1).tolist())),
        'structural_census': {'operators': {k.removeprefix('operator:'): v for k, v in types.items() if k.startswith('operator:')},
            'relations': {k.removeprefix('relation:'): v for k, v in types.items() if k.startswith('relation:')},
            'authority': 'exact typed input inventory; deterministic baseline'},
        'typed_observation_tokens': observation_tokens(observation), 'typed_observation_ids': [model.obs_vocab[x] for x in observation_tokens(observation)],
        'typed_graph_tokens': graph_tokens(graph), 'typed_graph_ids': [model.obs_vocab[x] for x in graph_tokens(graph)],
        'checkpoint_step': checkpoint['step'], 'checkpoint_sha256': hashlib.sha256(Path(checkpoint_path).read_bytes()).hexdigest(),
        'calibration': 'not established', 'native_semantic_admission': 'NOT_RUN'}

def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--source-run', type=Path)
    parser.add_argument('--predict', type=Path); parser.add_argument('--checkpoint', type=Path)
    parser.add_argument('--updates-per-record', type=int, default=2); args = parser.parse_args()
    if args.predict:
        if not args.checkpoint: parser.error('--predict requires --checkpoint')
        torch.set_num_threads(2)
        print(json.dumps(predict(args.predict, args.checkpoint), indent=2)); return
    if not 1 <= args.updates_per_record <= 100:
        raise ValueError('updates-per-record must be 1..100')
    torch.set_num_threads(2); torch.manual_seed(137); rng = random.Random(137)
    source_run = args.source_run or Path((LIFT / 'latest.txt').read_text().strip())
    payload = json.loads((source_run / 'candidate.json').read_text())
    native = graph_input(payload); fidelity = anchors(payload)
    run = ROOT / 'working/unified-shg-student' / str(time.time_ns()); run.mkdir(parents=True)
    (run / 'student-source.py').write_bytes(Path(__file__).read_bytes())
    (run / 'fixture-builder-source.py').write_bytes((LIFT / 'tower.py').read_bytes())
    tower = load_tower(run / 'fixture-builder-source.py'); data = dataset(tower)
    save(run / 'dataset.json', data)
    types = sorted({n['type'] for rows in data.values() for r in rows for n in r['graph']['nodes']} | {n['type'] for n in native['nodes']})
    roles = sorted({e['role'] for rows in data.values() for r in rows for e in r['graph']['incidences']} | {e['role'] for e in native['incidences']})
    model = Student(types, roles); initial = evaluate(model, data['validation']); incumbent = copy.deepcopy(model)
    best = initial['logloss']; best_step = step = 0; replay = []; history = []; start = time.monotonic()
    optimizer = torch.optim.AdamW(model.parameters(), lr=.002)
    ordered = list(data['train']); rng.shuffle(ordered)
    stream = (run / 'consumed.jsonl').open('w')
    for watermark, event in enumerate(ordered, 1):
        replay.append(event)
        stream.write(json.dumps({'watermark': watermark, 'id': event['id'], 'parent_group': event['parent_group'],
            'split': event['split'], 'structure_hash': event['structure_hash'], 'authority': event['authority']}) + '\n'); stream.flush()
        for _ in range(args.updates_per_record):
            rows = rng.sample(replay, min(12, len(replay)))
            model.train(); optimizer.zero_grad(set_to_none=True)
            logits, shapes = model(rows, graph_mask=rng.random() < .1, observation_mask=rng.random() < .5)
            loss = nn.functional.cross_entropy(logits, torch.tensor([r['label'] for r in rows]))
            loss += .3 * nn.functional.cross_entropy(shapes, torch.tensor([r['shape'] for r in rows]))
            loss.backward(); nn.utils.clip_grad_norm_(model.parameters(), 1); optimizer.step(); step += 1
        if watermark % 16 == 0 or watermark == len(ordered):
            result = evaluate(model, data['validation']); promoted = result['logloss'] < best
            if promoted:
                best = result['logloss']; incumbent = copy.deepcopy(model); best_step = step
            history.append({'watermark': watermark, 'step': step, 'validation': {k: v for k, v in result.items() if k != 'predictions'}, 'promoted': promoted})
            print(json.dumps({'watermark': watermark, 'step': step, 'validation_accuracy': result['accuracy'], 'validation_logloss': result['logloss'], 'promoted': promoted}), flush=True)
    stream.close()
    config = {'types': types, 'roles': roles, 'width': 16, 'graph_steps': 4, 'bottom_up_formula_encoding': True,
        'binding_features': 'scope-relative binder distance derived from binding/application incidences', 'transformer_layers': 1,
        'observation_vocabulary': model.obs_vocab, 'support_labels': ['unsupported', 'supported'], 'shape_labels': SHAPES}
    for name, m, s in [('live', model, step), ('incumbent', incumbent, best_step)]:
        torch.save({'state_dict': m.state_dict(), 'config': config, 'step': s}, run / (name + '.pt'))
    probes = []
    for i, shape in enumerate(SHAPES):
        g = native if i == 0 else controls(tower, shape, 0, 0, 1, 71)
        obs = real_observations(source_run, 'common_good' if i == 1 else 'per_choice')
        if i >= 2:
            obs = {}  # Actual observers were never asked about these controls.
        probes.append({'id': 'actual-fixture:' + shape, 'parent_group': payload['source_digest'], 'graph': g,
            'observations': obs, 'label': int(i == 0), 'shape': i,
            'typed_graph_tokens': graph_tokens(g),
            'authority': 'authored proof schema + independently evaluated countermodel; no native formal admission'})
    test = evaluate(incumbent, data['test'])
    ablations = {name: evaluate(incumbent, data['test'], **mask) for name, mask in
        [('graph_only', {'observation_mask': True}), ('observations_only', {'graph_mask': True}),
         ('both_masked', {'graph_mask': True, 'observation_mask': True})]}
    real = evaluate(incumbent, probes); real_masked = evaluate(incumbent, probes, observation_mask=True)
    pins = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in [source_run / 'candidate.json', source_run / 'native-checks.json',
        source_run / 'observations/results.json', run / 'fixture-builder-source.py', run / 'student-source.py', run / 'dataset.json', run / 'incumbent.pt']}
    report = {'schema': 'UnifiedSHGStudentPilotV1', 'run': str(run), 'source_run': str(source_run), 'pins': pins,
        'architecture': 'typed incidence graph encoder + bottom-up child composition + scope-relative binding features + typed observer token embeddings + one tiny transformer + support/shape heads',
        'device': 'cpu', 'parameters': sum(p.numel() for p in model.parameters()), 'steps': step, 'incumbent_step': best_step,
        'elapsed_seconds': time.monotonic() - start, 'data': {'actual_objects': len(payload['objects']), 'actual_source_groups': 1,
            'actual_native_coordinates': json.loads((source_run / 'native-checks.json').read_text())['resolved_addresses'],
            'generated_records': {k: len(v) for k, v in data.items()}, 'generated_parent_groups': {k: len(set(r['parent_group'] for r in v)) for k, v in data.items()},
            'test_scope': 'fresh generated quantifier depth 5/6 and justification depth 6/7; disjoint parent groups and structure hashes',
            'development_scope': 'depth 3/4, justification 4/5 reused to develop the input architecture; not an untouched test',
            'observer_training': 'SIMULATED noisy/correlated structural-control observations with field/observer dropout',
            'real_observer_training_examples': 0, 'learned_real_observer_consensus': False},
        'initial_validation': initial, 'history': history, 'test': test, 'input_mask_ablations_same_checkpoint': ablations,
        'majority_test_accuracy': max(collections.Counter(r['label'] for r in data['test']).values()) / len(data['test']),
        'symbolic_control_authority': 'Authored transformations and evaluated countermodels supply labels; model is not a verifier',
        'real_fixture_probe': real, 'real_fixture_without_observers': real_masked, 'source_fidelity': fidelity,
        'calibration': 'not established', 'native_semantic_admission': 'NOT_RUN', 'actual_corpus_heldout_accuracy': None,
        'promotion': 'validation logloss only; test and real fixture never used for promotion',
        'streaming': 'Each accepted train record enters replay and triggers updates before the next record; live and incumbent checkpoints retained',
        'pipeline_graph': {'nodes': [{'id': 'source', 'label': 'Source + native SHG: 88 objects'}, {'id': 'graph', 'label': 'Typed incidence encoder'},
            {'id': 'observers', 'label': 'Jev / Laya / Qwen observations'}, {'id': 'tokens', 'label': 'Typed bins + explicit missing'},
            {'id': 'student', 'label': 'Tiny transformer fusion'}, {'id': 'labels', 'label': 'Support + composition logits'},
            {'id': 'checks', 'label': 'Source / schema / countermodel checks'}, {'id': 'rg', 'label': 'ResearchGraph observations'}],
            'edges': [{'source': a, 'target': b} for a, b in [('source', 'graph'), ('observers', 'tokens'), ('graph', 'student'), ('tokens', 'student'), ('student', 'labels'), ('source', 'checks'), ('labels', 'rg'), ('checks', 'rg')]]}}
    save(run / 'report.json', report)
    save(run / 'real-input.json', {'source': payload['source'], 'graph': native, 'observations': probes[0]['observations'],
        'typed_tokens': observation_tokens(probes[0]['observations']), 'typed_graph_tokens': graph_tokens(native), 'source_fidelity': fidelity})
    save(run / 'real-probes.json', probes)
    save(run / 'predictions.json', {'test': test['predictions'], 'real_fixture': real['predictions'], 'real_fixture_without_observers': real_masked['predictions']})
    (run.parent / 'latest.txt').write_text(str(run) + '\n')
    save(ROOT / 'working/text-primitives/unified-student.json', report)
    print(json.dumps({k: report[k] for k in ['run', 'parameters', 'steps', 'incumbent_step', 'elapsed_seconds', 'data']}, indent=2))
    print('TEST', json.dumps({k: v for k, v in test.items() if k != 'predictions'}))
    print('REAL', json.dumps(real['predictions']))

if __name__ == '__main__':
    main()
