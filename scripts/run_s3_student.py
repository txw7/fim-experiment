"""Run the frozen student on retained S3 typed records; never execute the spec."""
import collections, hashlib, json, sqlite3, time
from pathlib import Path
import torch
import unified_shg_student as student

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path('/home/user0/shg_mu_workspace/project/semantic-slice/recent-s25-s3/S3')

def concept_examples(raw):
    # Authored diagnostic mappings, not model extraction or native admission.
    examples = [
        ('S3 should depend on S2.5 in stages.json, not merely S2.',
         ['stage:S3','stage:S2.5','stage:S2'],
         {'constraint':'required','relation':'depends-on','composition':'atomic dependency'},
         ['REQUIRED',['DEPENDS_ON','stage:S3','stage:S2.5']]),
        ('Limit to ONE explicitly requested live provider invocation',
         ['event:provider-invocation','stage:S3'],
         {'constraint':'cardinality','relation':'bounded-by','composition':'exactly-once'},
         ['REQUIRED',['COUNT_EQUALS', ['EVENTS_IN','stage:S3','event:provider-invocation'],1]]),
        ('If provider is unavailable, leave S3 OPEN and do not manufacture a positive.',
         ['provider:looper','stage:S3','state:OPEN','event:fabricated-positive'],
         {'constraint':'conditional obligations','relation':'condition-to-obligation','composition':'IF + AND + NOT'},
         ['IF',['NOT',['AVAILABLE','provider:looper']],['AND',['REQUIRED',['SET_STATE','stage:S3','state:OPEN']],['FORBIDDEN','event:fabricated-positive']]]),
        ('(SUPERVISE A0 (PARALLEL (PAIR B1 C1) (PAIR B2 C2)))',
         ['agent:A0','agent:B1','agent:C1','agent:B2','agent:C2'],
         {'constraint':'architecture','relation':'contains','composition':'supervision of two parallel pairs'},
         ['SUPERVISE','agent:A0',['PARALLEL',['PAIR','agent:B1','agent:C1'],['PAIR','agent:B2','agent:C2']]])]
    result=[]
    for quote, concepts, labels, symbolic in examples:
        start=raw.index(quote)
        result.append({'quote':quote,'char_start':start,'char_end':start+len(quote),
            'concept_refs':concepts,'proposed_dimensions':labels,'symbolic_candidate':symbolic,
            'authority':'authored example mapping; concept refs are analysis names, not runtime object IDs; NOT_RUN'})
    return result

def main():
    torch.set_num_threads(2)
    output = ROOT / 'working/unified-shg-student' / ('s3-spec-' + str(time.time_ns()))
    output.mkdir()
    run = Path((output.parent / 'latest.txt').read_text().strip())
    checkpoint = run / 'incumbent.pt'
    raw = (SOURCE / 'raw-spec.txt').read_text()
    envelope = next(x for x in json.loads((SOURCE.parent / 'sources.json').read_text()) if x['message_id'] == 'S3-original-spec')
    assert hashlib.sha256(raw.encode()).hexdigest() == envelope['source_sha256']
    connection = sqlite3.connect('file:' + str(SOURCE / 'full/slices.sqlite3') + '?mode=ro', uri=True)
    snapshot = sqlite3.connect(output / 'source.sqlite3')
    connection.backup(snapshot); connection.close()
    records = {}
    for payload, in snapshot.execute('SELECT payload FROM entries WHERE payload IS NOT NULL ORDER BY rowid'):
        value = json.loads(payload)
        if isinstance(value, dict) and isinstance(value.get('added'), dict):
            records[value['added']['id']] = value['added']
    snapshot.close()
    ids = list(records); index = {key:i for i,key in enumerate(ids)}
    assert ids and len(ids) == len(set(ids))
    verified = 0
    for obj in records.values():
        spans = obj.get('source_extents', [])
        if spans:
            quote = ''.join(raw[s['char_start']:s['char_end']] for s in spans)
            assert quote == obj['quote'], ('Anchor mismatch', obj['id'])
            verified += 1
    query = 'w0:n2'
    assert query in index
    graph = {'native_ids': ids, 'query_native_id': query,
        'nodes': [{'type': o['kind'] + ':' + o.get('operator', ''), 'value_type':o.get('value_type','none'),
            'query_target':o['id'] == query} for o in records.values()], 'incidences':[]}
    for obj in records.values():
        for pos, edge in enumerate(obj.get('participants', [])):
            assert edge['target'] in index
            graph['incidences'].append({'relation':index[obj['id']], 'participant':index[edge['target']],
                'role':edge['role'], 'position':edge.get('position',pos)})
    session = SOURCE / 'full/e90b2562985840bffc858285099939751954f812029cb5e7b28f22f41398597b'
    retained = {}
    for name in ('jev','laya'):
        retained[name] = {part:json.loads((session / f'observers-w0-0/{name}/{part}.json').read_text()) for part in ('request','response')}
    retained['qwen'] = {part:json.loads((session / f'w0/classify/{part}.json').read_text()) for part in ('request','response')}
    observations = {name:{'answers':{'support':retained[name]['response']['answers'][query]},
        'origin':'retained S3 observation, not a fresh API call'} for name in ('jev','laya')}
    packet = {'graph':graph,'observations':observations,'source':raw,'source_envelope':envelope,
        'semantic_objects':list(records.values()), 'source_fidelity':'exact spans only; native admission NOT_RUN'}
    student.save(output / 'input.json',packet)
    config = torch.load(checkpoint,map_location='cpu',weights_only=True)['config']
    unknown = {'node_types':sorted({n['type'] for n in graph['nodes']} - set(config['types'])),
        'value_types':sorted({n['value_type'] for n in graph['nodes']} - {'none','Individual','Proposition','ProofCandidate','JustificationCandidate'}),
        'incidence_roles':sorted({e['role'] for e in graph['incidences']} - set(config['roles']))}
    start=time.monotonic()
    try:
        result={'state':'SCORED','output':student.predict(output/'input.json',checkpoint)}
    except (KeyError,ValueError) as exc:
        result={'state':'BLOCKED_INPUT_DOMAIN','exception_type':type(exc).__name__,'exception':str(exc),
            'raw_logits':None,'reason':'Frozen vocabulary and choice-composition heads do not cover S3 spec objects. No coercion, replacement vocabulary or retraining.'}
    assert result['state']=='BLOCKED_INPUT_DOMAIN' and result['raw_logits'] is None, 'Expected an explicit unsupported-domain result'
    types=collections.Counter(o['kind'] for o in records.values())
    classifications=json.loads(retained['qwen']['response']['choices'][0]['message']['content'])
    cases=[]
    for key in ('w0:n0','w0:n1','w0:n2','w0:n3'):
        cases.append({'id':key,'source_quote':records[key]['quote'],'exact_anchor':True,
            'jev':retained['jev']['response']['answers'][key], 'laya':retained['laya']['response']['answers'][key]})
    paths=[SOURCE/'raw-spec.txt',SOURCE.parent/'sources.json',output/'source.sqlite3',checkpoint,Path(__file__),ROOT/'scripts/unified_shg_student.py']
    for name in ('jev','laya'):
        paths += [session/f'observers-w0-0/{name}/{part}.json' for part in ('request','response')]
    paths += [session/f'w0/classify/{part}.json' for part in ('request','response')]
    report={'schema':'ExternalSHGStudentProbeV1','run':str(output),'spec':'S3_LIVE_AB','source_path':str(SOURCE/'raw-spec.txt'),
        'source_sha256':envelope['source_sha256'],'source':raw,'source_characters':len(raw),'retained_window_scope':'Existing w0 extraction only; not full-spec coverage',
        'objects':list(records.values()),'graph':graph,'object_kinds':dict(types),'exact_anchors_verified':verified,
        'relation_as_operand':any(records[ids[e['participant']]]['kind'] in ('inference','network-composition','relation-composition') for e in graph['incidences']),
        'query':{'id':query,'quote':records[query]['quote']},'checkpoint':str(checkpoint),'checkpoint_label_space':student.SHAPES,
        'unknown_input_features':unknown,'student':result,'inference_attempt_seconds':time.monotonic()-start,
        'typed_observation_tokens':student.observation_tokens(observations),'observer_calls_this_run':0,'retained_observer_cases':cases,
        'retained_requests_and_responses':retained,'qwen_document_type':classifications.get('document_type'),
        'expected_document_type':envelope['document_type'],'document_type_match':classifications.get('document_type')==envelope['document_type'],
        'concept_mapping':concept_examples(raw),
        'native_semantic_admission':'NOT_RUN','training_updates':0,'spec_instructions_executed':False,
        'pins':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    student.save(output/'report.json', report)
    student.save(ROOT/'working/text-primitives/unified-spec-trial.json', report)
    print(json.dumps({k:report[k] for k in ('run','spec','object_kinds','exact_anchors_verified','unknown_input_features','student','document_type_match')},indent=2))

if __name__=='__main__':main()
