"""Archive the external S3 input-domain experiment in the existing ResearchGraph."""
import copy, hashlib, json
from pathlib import Path
from register_unified_student import (ROOT, GRAPH, RecursiveCASRepository, Transaction, new_object,
    cas_ref, blob_ref, dataset, observation, hypothesis, research_question, experiment_run,
    experiment, research_program, validate_research_root)

report_path = ROOT / 'working/text-primitives/unified-spec-trial.json'
report = json.loads(report_path.read_text()); run = Path(report['run'])
if (run / 'research-graph-receipt.json').exists():
    print((run / 'research-graph-receipt.json').read_text())
else:
    for path, sha in report['pins'].items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == sha, 'Changed pin: ' + path
    repo = RecursiveCASRepository(GRAPH); base=repo.head
    old=repo.get_revision(repo.root_revision(base)); content=copy.deepcopy(old['content'])
    prefix='s3-student-probe:'+run.name
    frozen=Path(report['checkpoint']).parent.name
    model_ref=content['models']['model:unified-shg-student:'+frozen+':incumbent']
    refs={}
    for name in ('report.json','input.json','source.sqlite3'):
        raw=(run/name).read_bytes(); sha=hashlib.sha256(raw).hexdigest()
        obj=new_object('artifact:'+prefix+':'+name,kind='artifact',schema='ArtifactV1',
            value={'name':name,'sha256':sha,'bytes':len(raw),'payload':blob_ref(repo.blobs.put(raw))},
            authority={'evidence_class':'source_evidence','review_state':'accepted'})
        ref=cas_ref(repo.put_canonical(obj,commit_id=base),obj['id'])
        content['artifacts'][obj['id']]=ref; refs[name]=ref
        assert hashlib.sha256(repo.blobs.get(obj['value']['payload']['$blob'])).hexdigest()==sha
    ds=dataset('dataset:'+prefix,'S3 retained typed input and observer records',task='frozen vocabulary compatibility test',
        content_digest=report['source_sha256'],split_policy={'evaluation_only':True,'training_updates':0,'coverage':report['retained_window_scope']})
    ds_ref=cas_ref(repo.put_canonical(ds,commit_id=base),ds['id']); content['datasets'][ds['id']]=ds_ref
    h=hypothesis('hypothesis:'+prefix,'The quantified-choice student can accept this external S3 typed graph without changing its vocabulary or label space.')
    question=research_question('question:'+prefix,'Does the frozen student accept the S3 spec graph?',hypotheses=[h])
    eid,rid='experiment:'+prefix,'run:'+prefix
    obs=observation('observation:'+prefix,rid,'external_spec_input_compatibility',
        {k:report[k] for k in ('student','unknown_input_features','document_type_match','observer_calls_this_run','training_updates','native_semantic_admission')},
        artifact_ref=refs['report.json'])
    execution=experiment_run(rid,eid,observations=[obs],configuration={'pins':report['pins'],'spec_instructions_executed':False})
    exp=experiment(eid,'Frozen student on S3_LIVE_AB',h['id'],runs=[execution],source_pins=[refs['input.json']],
        dataset_pins=[ds_ref],model_pins=[model_ref],design={'no_type_coercion':True,'no_retraining':True})
    program=research_program('program:'+prefix,'S3 external student input probe',questions=[question],experiments=[exp])
    content['research_programs'][program['id']]=cas_ref(repo.put_canonical(program,commit_id=base),program['id'])
    root=new_object(old['id'],kind=old['kind'],schema=old['schema'],value=old['value'],content=content,
        authority=old['authority'],links=old['links'],provenance=old['provenance'],annotations=old['annotations'])
    assert validate_research_root(repo,repo.put_canonical(root,commit_id=base))
    commit=repo.commit(base,Transaction(base_commit=base,root=root,metadata={'source':'s3-student-input-probe','run':str(run)}))
    receipt={'graph':str(GRAPH),'commit':commit,'parent_commit':base,'research_root_validated':True,
        'artifacts':refs,'stored_bytes_verified':True,'result':'BLOCKED_INPUT_DOMAIN','native_semantic_admission':'NOT_RUN'}
    (run/'research-graph-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    report['research_graph']=receipt
    report_path.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))
