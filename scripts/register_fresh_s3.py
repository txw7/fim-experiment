"""Retain fresh tower evidence and actual trained checkpoints in the existing RG."""
import copy, hashlib, json
from pathlib import Path
from register_unified_student import (ROOT, GRAPH, RecursiveCASRepository, Transaction, new_object,
 cas_ref, blob_ref, dataset, model, method, hypothesis, research_question, observation,
 experiment_run, experiment, research_program, validate_research_root)

def main():
 run=Path((ROOT/'working/fresh-s3-tower/latest.txt').read_text().strip())
 report=json.loads((run/'report.json').read_text())
 for p,digest in report['pins'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==digest,p
 repo=RecursiveCASRepository(GRAPH);base=repo.head;prefix='fresh-s3-tower:'+run.name
 artifacts=[]
 def put(o):return cas_ref(repo.put_canonical(o,commit_id=base),o['id'])
 requests={str(p.relative_to(run)):json.loads(p.read_text()) for p in run.glob('s3-p*/*/*/*.json')}
 bundle={'report':report,'fresh_requests_and_responses':requests,'runner_source':(run/'runner-source.py').read_text(),'source':(run/'source.txt').read_text(),'checkpoint_replay':json.loads((run/'checkpoint-replay.json').read_text())}
 (run/'evidence-bundle.json').write_text(json.dumps(bundle,indent=2)+'\n')
 for path in [run/'evidence-bundle.json',run/'initial.pt',run/'live.pt',run/'incumbent.pt']:
  raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest();blob=repo.blobs.put(raw)
  assert hashlib.sha256(repo.blobs.get(blob)).hexdigest()==digest
  o=new_object('artifact:'+prefix+':'+path.name,kind='artifact',schema='ArtifactV1',value={'name':path.name,'sha256':digest,'bytes':len(raw),'payload':blob_ref(blob),'capture':'fresh empirical tower evidence; no semantic admission'},authority={'evidence_class':'source_evidence','review_state':'accepted'})
  artifacts.append((o,put(o)))
 evidence=artifacts[0][1]
 ds=dataset('dataset:'+prefix,'Fresh S3 source paragraph profiles',task='four-dimensional structural classification',content_digest=report['source_sha256'],split_policy={'train':4,'validation':1,'test':1,'group':'source paragraph','single_document':True,'labels':'fresh Qwen feedback pseudo-labels, not gold'})
 ds['links']=[{'relation':'derived_from','domain':'provenance','target':evidence}];dsref=put(ds)
 models=[]
 for name,step,artifact in [('live',report['training_steps'],artifacts[2][1]),('incumbent',report['incumbent_step'],artifacts[3][1])]:
  m=model('model:'+prefix+':'+name,'Fresh S3 tiny student '+name,family='tiny-typed-graph-transformer',architecture={'parameters':report['parameters'],'step':step,'heads':report['heads'],'fresh_initialization':True},weights_ref=artifact);models.append((m,put(m)))
 met=method('method:'+prefix,'Fresh observations and interior replay training',method_family='streaming-teacher-student',parameters={'fresh_calls':report['fresh_calls'],'retained_responses_used':0,'interior_training_verified':True},version='v1');metref=put(met)
 h=hypothesis('hypothesis:'+prefix,'A fresh student can train inside the S3 observer-feedback loop.',scope={'single_spec_pipeline_test':True,'native_semantic_admission':'NOT_RUN'})
 question=research_question('question:'+prefix,'Did optimizer updates occur between fresh observer and feedback calls?',hypotheses=[h]);rid='run:'+prefix;eid='experiment:'+prefix
 obs=observation('observation:'+prefix,rid,'fresh_training_steps_weights_and_raw_logits',report,artifact_ref=evidence)
 r=experiment_run(rid,eid,observations=[obs],configuration={'steps':report['training_steps'],'source_pin':report['source_sha256'],'test_used_for_promotion':False})
 exp=experiment(eid,'Fresh S3 interior student training',h['id'],runs=[r],dataset_pins=[dsref],model_pins=[ref for _,ref in models],method_pins=[metref],source_pins=[evidence],design={'single_document_paragraph_split':True},acceptance_criteria={'training':'2000 actual optimizer steps and changed weights','ordering':'training before fresh feedback calls'})
 program=research_program('program:'+prefix,'Fresh S3 tower and trained students',questions=[question],experiments=[exp],description='Empirical training evidence; pseudo-label agreement is not semantic correctness.')
 pref=put(program);old=repo.get_revision(repo.root_revision(base));content=copy.deepcopy(old['content'])
 content['research_programs'][program['id']]=pref;content['datasets'][ds['id']]=dsref;content['methods'][met['id']]=metref
 for o,ref in models:content['models'][o['id']]=ref
 for o,ref in artifacts:content['artifacts'][o['id']]=ref
 root=new_object(old['id'],kind=old['kind'],schema=old['schema'],value=old['value'],content=content,authority=old['authority'],links=old['links'],provenance=old['provenance'],annotations=old['annotations'])
 assert validate_research_root(repo,repo.put_canonical(root,commit_id=base))
 commit=repo.commit(base,Transaction(base_commit=base,root=root,metadata={'source':'fresh-s3-tower','run':str(run),'preserve_existing_programs':True}))
 assert validate_research_root(repo,repo.root_revision(commit))
 receipt={'graph':str(GRAPH),'parent_commit':base,'commit':commit,'source_and_checkpoint_bytes_verified':True,'fresh_calls':report['fresh_calls'],'training_steps':report['training_steps'],'native_semantic_admission':'NOT_RUN','existing_programs_preserved':True}
 (run/'research-graph-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))

if __name__=='__main__':main()
