"""Archive the shared tower, actual teacher evidence, features and trained forks."""
import copy,hashlib,json
from pathlib import Path
from register_unified_student import ROOT,GRAPH,RecursiveCASRepository,Transaction,new_object,cas_ref,blob_ref,dataset,model,method,hypothesis,research_question,observation,experiment_run,experiment,research_program,validate_research_root

def main():
 run=Path((ROOT/'working/philosophy-spec-bridge/latest.txt').read_text().strip());report=json.loads((run/'report.json').read_text())
 for p,h in report['pins'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
 for p,h in report['neural']['pins'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
 for name in ['symbolic','probabilistic']:
  old=report['original_student_models'][name];assert hashlib.sha256((run/('origin-'+name+'.pt')).read_bytes()).hexdigest()==old['snapshot_sha256'],'Origin snapshot changed'
 repo=RecursiveCASRepository(GRAPH);base=repo.head;prefix='philosophy-spec-bridge:'+run.name
 def put(o):return cas_ref(repo.put_canonical(o,commit_id=base),o['id'])
 files={str(p.relative_to(run)):p.read_text() for p in run.rglob('*') if p.is_file() and p.suffix in ['.json','.jsonl','.csv','.py','.txt'] and p.name!='evidence-bundle.json'}
 bundle={'report':report,'captured_artifacts':files,'source_instructions_are_data':True};(run/'evidence-bundle.json').write_text(json.dumps(bundle,ensure_ascii=False)+'\n');artifacts=[]
 for p in [run/'evidence-bundle.json',run/'symbolic-bridge.pt',run/'probabilistic-bridge.pt',run/'origin-symbolic.pt',run/'origin-probabilistic.pt',run/'symbolic-initial.pt',run/'probabilistic-initial.pt',run/'neural/operator-snapshots/incumbent.pt',run/'neural/operator-snapshots/live.pt']:
  raw=p.read_bytes();digest=hashlib.sha256(raw).hexdigest();blob=repo.blobs.put(raw);assert hashlib.sha256(repo.blobs.get(blob)).hexdigest()==digest
  o=new_object('artifact:'+prefix+':'+p.name,kind='artifact',schema='ArtifactV1',value={'name':p.name,'sha256':digest,'bytes':len(raw),'payload':blob_ref(blob),'capture':'Actual features, fresh requests, logits and optimizer checkpoints; no native semantic admission'},authority={'evidence_class':'source_evidence','review_state':'accepted'});artifacts.append((o,put(o)))
 evidence=artifacts[0][1];ds=dataset('dataset:'+prefix,'S3 shared philosophy feature lane',task='26 logic heads, 18 interpretation axes, eight spec features and original structural rubrics',content_digest=report['source_sha256'],split_policy={'train':4,'validation':1,'test':1,'whole_source_holdout':False,'single_source_pilot':True,'labels':'Qwen pseudo-labels and Jev distillation distributions, not gold'});dsref=put(ds)
 models=[]
 for i,name in enumerate(['symbolic','probabilistic'],1):
  s=report['new_students'][name];o=model('model:'+prefix+':'+name,'Philosophy checkpoint fork '+name,family='micro-transformer-typed-feature-fusion',architecture={'parameters':s['parameters'],'steps':s['steps'],'frozen_step':s['frozen_step'],'heads':report['logic_groups'],'feature_dimensions':report['feature_dimensions'],'original_checkpoint':report['original_student_models'][name],'initialization':'Original frozen philosophy reader plus zero-initialized continuous feature projection'},weights_ref=artifacts[i][1]);models.append((o,put(o)))
 met=method('method:'+prefix,'Shared original philosophy inventories and native distributions',method_family='coupled-three-layer-symbolic-probabilistic-tower',parameters={'fresh_calls':report['fresh_calls'],'interior_training':'250 updates/student before and after each feedback; 1500 each','feature_masks':True,'checkpoint_replay_verified':report['checkpoint_replay_verified'],'coverage':report['coverage']},version='v1');metref=put(met)
 h=hypothesis('hypothesis:'+prefix,'Original philosophy representations can condition a typed specification student.',scope={'S3_pilot':True,'generalization_not_established':True});q=research_question('question:'+prefix,'What transfers and fails when the complete operational philosophy lane processes S3?',hypotheses=[h]);rid='run:'+prefix;eid='experiment:'+prefix
 obs=observation('observation:'+prefix,rid,'native_observations_classifier_logits_compositions_and_actual_training',report,artifact_ref=evidence);r=experiment_run(rid,eid,observations=[obs],configuration={'source_pin':report['source_sha256'],'students':report['new_students'],'fresh_calls':report['fresh_calls']})
 exp=experiment(eid,'Philosophy to spec bridge',h['id'],runs=[r],dataset_pins=[dsref],model_pins=[ref for _,ref in models],method_pins=[metref],source_pins=[evidence],design={'single_source_paragraph_split':True,'teacher_features_masked_ablation':True},acceptance_criteria={'execution':'Original inventories used, actual updates and exact requests retained','semantic':'Source graph and symbolic proposals remain candidates'})
 program=research_program('program:'+prefix,'Shared philosophy and specification tower',questions=[q],experiments=[exp],description='All operational stages reused; unavailable wishlist stages identified separately.');pref=put(program)
 old=repo.get_revision(repo.root_revision(base));content=copy.deepcopy(old['content']);content['research_programs'][program['id']]=pref;content['datasets'][ds['id']]=dsref;content['methods'][met['id']]=metref
 for o,ref in models:content['models'][o['id']]=ref
 for o,ref in artifacts:content['artifacts'][o['id']]=ref
 root=new_object(old['id'],kind=old['kind'],schema=old['schema'],value=old['value'],content=content,authority=old['authority'],links=old['links'],provenance=old['provenance'],annotations=old['annotations']);assert validate_research_root(repo,repo.put_canonical(root,commit_id=base))
 commit=repo.commit(base,Transaction(base_commit=base,root=root,metadata={'source':'philosophy-spec-bridge','run':str(run),'preserve_existing_programs':True}));assert validate_research_root(repo,repo.root_revision(commit))
 receipt={'graph':str(GRAPH),'parent_commit':base,'commit':commit,'source_and_checkpoint_bytes_verified':True,'steps':{n:s['steps'] for n,s in report['new_students'].items()},'native_semantic_admission':'NOT_RUN','existing_programs_preserved':True};(run/'research-graph-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
if __name__=='__main__':main()
