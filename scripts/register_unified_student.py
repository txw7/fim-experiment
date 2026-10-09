"""Append the measured pilot and its logits to the existing ResearchGraph."""
import copy, hashlib, json, sys
from pathlib import Path
sys.path.insert(0, '/home/user0/worktrees/research-laya-qwen-rg-ingestion-v1/corpusGraph')
from recursive_cas import RecursiveCASRepository, Transaction, cas_ref, blob_ref, new_object
from recursive_cas.research import (dataset, model, method, observation, hypothesis,
    research_question, experiment_run, experiment, research_program, validate_research_root)

ROOT = Path(__file__).resolve().parents[1]
GRAPH = Path('/home/user0/.local/state/turn-transport/philosopher-text-structure-v1/research-graph')

def retain_observer_prompts(run, receipt):
    if 'observer_prompts' in receipt:
        return receipt
    report = json.loads((run / 'report.json').read_text())
    folder = Path(report['source_run']) / 'observations'
    paths = [folder / (name + '-request.json') for name in ('jev', 'laya', 'qwen', 'qwen-feedback')]
    bundle = {'scope': 'retained observer requests for the original source comparison; no new observer calls',
        'requests': {p.name.removesuffix('-request.json'): json.loads(p.read_text()) for p in paths},
        'pins': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        'responses': json.loads((folder / 'results.json').read_text())}
    path = run / 'observer-prompts.json'
    path.write_text(json.dumps(bundle, indent=2) + '\n')
    repo = RecursiveCASRepository(GRAPH); base = repo.head
    old = repo.get_revision(repo.root_revision(base)); content = copy.deepcopy(old['content'])
    program = content['research_programs']['program:unified-shg-student:' + run.name]
    raw = path.read_bytes(); sha = hashlib.sha256(raw).hexdigest()
    obj = new_object('artifact:unified-shg-student:' + run.name + ':observer-prompts',
        kind='artifact', schema='ArtifactV1', value={'name': path.name, 'sha256': sha,
            'bytes': len(raw), 'payload': blob_ref(repo.blobs.put(raw)),
            'capture': bundle['scope'], 'request_pins': bundle['pins']},
        links=[{'relation': 'derived_from', 'domain': 'provenance', 'target': program}],
        authority={'evidence_class': 'source_evidence', 'review_state': 'accepted'})
    revision = repo.put_canonical(obj, commit_id=base)
    content['artifacts'][obj['id']] = cas_ref(revision, obj['id'])
    root = new_object(old['id'], kind=old['kind'], schema=old['schema'], value=old['value'], content=content,
        authority=old['authority'], links=old['links'], provenance=old['provenance'], annotations=old['annotations'])
    assert validate_research_root(repo, repo.put_canonical(root, commit_id=base))
    commit = repo.commit(base, Transaction(base_commit=base, root=root,
        metadata={'source': 'unified-shg-observer-prompt-snapshot', 'run': str(run)}))
    stored = repo.get_revision(revision)
    assert hashlib.sha256(repo.blobs.get(stored['value']['payload']['$blob'])).hexdigest() == sha
    receipt['observer_prompts'] = {'commit': commit, 'artifact_revision': revision, 'sha256': sha,
        'file': str(path), 'four_exact_requests_and_responses_retained': True, 'bytes_verified': True}
    (run / 'research-graph-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt

def main():
    run = Path((ROOT / 'working/unified-shg-student/latest.txt').read_text().strip())
    if (run / 'research-graph-receipt.json').exists():
        print(json.dumps(retain_observer_prompts(run, json.loads((run / 'research-graph-receipt.json').read_text())), indent=2)); return
    report = json.loads((run / 'report.json').read_text())
    for path, expected in report['pins'].items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, 'Pin changed: ' + path
    repo = RecursiveCASRepository(GRAPH); base = repo.head
    assert base is not None, 'Expected the existing four-corpus ResearchGraph'
    prefix = 'unified-shg-student:' + run.name
    def put(obj):
        return cas_ref(repo.put_canonical(obj), obj['id'])
    artifacts = {}
    paths = [Path(p) for p in report['pins']] + [run / f for f in
        ('live.pt', 'report.json', 'real-input.json', 'real-probes.json', 'predictions.json', 'consumed.jsonl', 'prediction-replay.json')]
    for path in dict.fromkeys(paths):
        raw = path.read_bytes(); sha = hashlib.sha256(raw).hexdigest()
        ident = 'artifact:' + prefix + ':' + hashlib.sha256(str(path).encode()).hexdigest()[:16]
        obj = new_object(ident, kind='artifact', schema='ArtifactV1', value={'name': path.name,
            'path_at_capture': str(path), 'sha256': sha, 'bytes': len(raw), 'payload': blob_ref(repo.blobs.put(raw)),
            'capture': 'immutable empirical input/output snapshot; no semantic admission'},
            authority={'evidence_class': 'source_evidence', 'review_state': 'accepted'})
        artifacts[str(path)] = (obj, put(obj))
    def ref(path): return artifacts[str(path)][1]
    def edge(target): return {'relation': 'derived_from', 'domain': 'provenance', 'target': target}
    ds = dataset('dataset:' + prefix, 'Generated SHG composition controls plus one real fixture probe',
        task='typed input/composition classification pilot', content_digest=report['pins'][str(run / 'dataset.json')],
        split_policy={**report['data'], 'real_fixture_training': False, 'authority': report['symbolic_control_authority']})
    ds['links'] = [edge(ref(run / 'dataset.json')), edge(ref(Path(report['source_run']) / 'candidate.json'))]
    ds_ref = put(ds)
    models = []
    for name, step in [('incumbent', report['incumbent_step']), ('live', report['steps'])]:
        obj = model('model:' + prefix + ':' + name, 'Typed graph/observer student · ' + name,
            family='tiny-graph-transformer', architecture={'description': report['architecture'],
                'parameters': report['parameters'], 'step': step, 'device': 'cpu', 'calibration': 'not established'},
            weights_ref=ref(run / (name + '.pt')))
        models.append((obj, put(obj)))
    met = method('method:' + prefix, 'Typed incidences, bottom-up composition, observer projection and streaming replay',
        method_family='neurosymbolic-input-classification', parameters={'scope': report['data'],
            'promotion': report['promotion'], 'source_fidelity': report['source_fidelity']}, version='v1')
    met['links'] = [edge(ref(run / 'student-source.py')), edge(ref(run / 'fixture-builder-source.py'))]
    met_ref = put(met)
    h = hypothesis('hypothesis:' + prefix, 'Typed graph and observer features can jointly condition a tiny composition student.',
        scope={'generated_control_pilot': True, 'real_observer_consensus_trained': False, 'native_semantic_admission': 'NOT_RUN'})
    question = research_question('question:' + prefix, 'Does the combined input pipeline learn structural composition beyond a majority baseline?', hypotheses=[h])
    rid, eid = 'run:' + prefix, 'experiment:' + prefix
    observations = []
    for part, rows in [('generated-test', report['test']['predictions']), ('fixture-probe', report['real_fixture_probe']['predictions'])]:
        for i, prediction in enumerate(rows):
            obs = observation('observation:' + prefix + ':' + part + ':' + str(i), rid,
                'student_raw_logits_and_structural_diagnostic_target', {**prediction,
                    'scope': part, 'score_authority': 'experimental classifier output, uncalibrated; not semantic proof',
                    'input_label_authority': report['symbolic_control_authority'], 'native_admission': 'NOT_RUN'},
                artifact_ref=ref(run / 'predictions.json'))
            obs['links'].extend([edge(models[0][1]), edge(ds_ref), edge(ref(run / 'real-probes.json') if part == 'fixture-probe' else ref(run / 'dataset.json'))])
            observations.append(obs)
    summary = observation('observation:' + prefix + ':metrics', rid, 'controlled_pilot_metrics_and_input_mask_ablations',
        {k: report[k] for k in ('data', 'parameters', 'steps', 'test', 'input_mask_ablations_same_checkpoint',
            'majority_test_accuracy', 'actual_corpus_heldout_accuracy', 'native_semantic_admission')}, artifact_ref=ref(run / 'report.json'))
    observations.append(summary)
    run_obj = experiment_run(rid, eid, observations=observations, configuration={'code_and_input_pins': report['pins'],
        'live_and_incumbent_steps': [report['steps'], report['incumbent_step']], 'test_used_for_promotion': False})
    exp = experiment(eid, 'Combined SHG/typed-observer student pilot', h['id'], runs=[run_obj],
        dataset_pins=[ds_ref], model_pins=[r for _, r in models], method_pins=[met_ref],
        source_pins=[ref(Path(report['source_run']) / 'candidate.json')], design=report['data'],
        acceptance_criteria={'plumbing': 'typed references and nulls preserved; parent splits disjoint',
            'performance': 'measured against majority baseline; no corpus generalization claim'})
    program = research_program('program:' + prefix, 'Typed SHG compositions and observer-conditioned student',
        questions=[question], experiments=[exp], description='Empirical pilot; model outputs do not promote source interpretations.')
    program_ref = put(program)
    old = repo.get_revision(repo.root_revision(base)); content = copy.deepcopy(old['content'])
    content['research_programs'][program['id']] = program_ref
    content['datasets'][ds['id']] = ds_ref; content['methods'][met['id']] = met_ref
    for obj, rev in models: content['models'][obj['id']] = rev
    for obj, rev in artifacts.values(): content['artifacts'][obj['id']] = rev
    root = new_object(old['id'], kind=old['kind'], schema=old['schema'], value=old['value'], content=content,
        authority=old['authority'], links=old['links'], provenance=old['provenance'], annotations=old['annotations'])
    assert validate_research_root(repo, repo.put_canonical(root, commit_id=base))
    commit = repo.commit(base, Transaction(base_commit=base, root=root,
        metadata={'source': 'unified-shg-student-pilot', 'run': str(run), 'preserve_existing_programs': True}))
    revision = repo.root_revision(commit)
    assert validate_research_root(repo, revision)
    for obj, rev in artifacts.values():
        stored = repo.get_revision(rev['$cas'])
        assert hashlib.sha256(repo.blobs.get(stored['value']['payload']['$blob'])).hexdigest() == stored['value']['sha256']
    assert repo.head == commit
    receipt = {'graph': str(GRAPH), 'parent_commit': base, 'commit': commit, 'root_revision': revision,
        'observations': len(observations), 'raw_logit_observations': len(observations) - 1,
        'artifacts': len(artifacts), 'source_and_checkpoint_bytes_verified': True,
        'research_root_validated': True, 'native_semantic_admission': 'NOT_RUN', 'existing_programs_preserved': True}
    (run / 'research-graph-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(retain_observer_prompts(run, receipt), indent=2))

if __name__ == '__main__': main()
