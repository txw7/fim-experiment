"""Append actual connectivity training, logits and checkpoints to ResearchGraph."""
import copy,hashlib,json
from pathlib import Path
from register_unified_student import (ROOT,GRAPH,RecursiveCASRepository,Transaction,new_object,cas_ref,blob_ref,dataset,model,method,hypothesis,research_question,observation,experiment_run,experiment,research_program,validate_research_root)

def main():
 run=Path((ROOT/'working/connectivity-student/latest.txt').read_text().strip());report=json.loads((run/'report.json').read_text())
 for p,digest in report['pins'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==digest,p
 repo=RecursiveCASRepository(GRAPH);base=repo.head;prefix='connectivity-student:'+run.name
 def put(o):return cas_ref(repo.put_canonical(o,commit_id=base),o['id'])
 bundle={'report':report,'controls':json.loads((run/'controls.json').read_text()),'runner_source':(run/'runner-source.py').read_text(),'verification_source':(ROOT/'scripts/verify_connectivity_student.py').read_text(),'requests_responses':{str(p.relative_to(run)):json.loads(p.read_text()) for p in run.glob('connectivity-architecture/*/*/*.json')}}
 (run/'evidence-bundle.json').write_text(json.dumps(bundle,indent=2)+'\n');artifacts=[]
 for path in [run/'evidence-bundle.json',run/'initial.pt',run/'live.pt',run/'incumbent.pt']:
  raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest();blob=repo.blobs.put(raw);assert hashlib.sha256(repo.blobs.get(blob)).hexdigest()==digest
  o=new_object('artifact:'+prefix+':'+path.name,kind='artifact',schema='ArtifactV1',value={'name':path.name,'sha256':digest,'bytes':len(raw),'payload':blob_ref(blob),'capture':'actual training and connectivity measurements; no native admission'},authority={'evidence_class':'source_evidence','review_state':'accepted'});artifacts.append((o,put(o)))
 evidence=artifacts[0][1];ds=dataset('dataset:'+prefix,'Typed connectivity compositions and held-out source graph',task='directed incidences, binding, scope, positions and depth',content_digest=report['pins'][str(run/'controls.json')],split_policy={'train':80,'validation':16,'test':16,'canonical_composition_patterns_disjoint':True,'S3_source_training':False,'controls':'generated grammar targets','S3':'authored candidates, not gold'});dsref=put(ds)
 models=[]
 for name,step,artifact in [('live',2000,artifacts[2][1]),('incumbent',report['incumbent_step'],artifacts[3][1])]:
  o=model('model:'+prefix+':'+name,'Connectivity tiny transformer '+name,family='typed-structural-transformer-pair-decoder',architecture={'parameters':report['parameters'],'step':step,'heads':report['heads'],'fresh_initialization':True,'input':'typed structural serialization with identity references'},weights_ref=artifact);models.append((o,put(o)))
 met=method('method:'+prefix,'Typed occurrences and canonical identity bindings',method_family='structured-connectivity-reading',parameters={'fresh_calls':report['fresh_calls'],'loss':'directed presence plus role, position, depth and relation losses','interior_training_order_verified':True},version='v1');metref=put(met)
 h=hypothesis('hypothesis:'+prefix,'A tiny typed reader can learn connectivity beyond coarse paragraph labels.',scope={'generated_controls':True,'S3_candidate_not_gold':True});question=research_question('question:'+prefix,'Which directed incidences and operand bindings does the student recover?',hypotheses=[h]);rid='run:'+prefix;eid='experiment:'+prefix
 obs=observation('observation:'+prefix,rid,'connectivity_metrics_raw_logits_and_training_evidence',report,artifact_ref=evidence);r=experiment_run(rid,eid,observations=[obs],configuration={'steps':2000,'source_pin':report['source_sha256'],'S3_used_for_training_or_promotion':False})
 exp=experiment(eid,'Connectivity student versus exact typed incidences',h['id'],runs=[r],dataset_pins=[dsref],model_pins=[ref for _,ref in models],method_pins=[metref],source_pins=[evidence],design={'whole_composition_split':True},acceptance_criteria={'structural':'canonical identity and occurrence positions preserved','measurement':'endpoint F1 plus full incidence F1 reported separately'})
 program=research_program('program:'+prefix,'Low-dimensional connectivity heads over composed objects',questions=[question],experiments=[exp],description='Actual trained student; source graph and predictions remain candidates.');pref=put(program)
 old=repo.get_revision(repo.root_revision(base));content=copy.deepcopy(old['content']);content['research_programs'][program['id']]=pref;content['datasets'][ds['id']]=dsref;content['methods'][met['id']]=metref
 for o,ref in models:content['models'][o['id']]=ref
 for o,ref in artifacts:content['artifacts'][o['id']]=ref
 root=new_object(old['id'],kind=old['kind'],schema=old['schema'],value=old['value'],content=content,authority=old['authority'],links=old['links'],provenance=old['provenance'],annotations=old['annotations']);assert validate_research_root(repo,repo.put_canonical(root,commit_id=base))
 commit=repo.commit(base,Transaction(base_commit=base,root=root,metadata={'source':'connectivity-student','run':str(run),'preserve_existing_programs':True}));assert validate_research_root(repo,repo.root_revision(commit))
 receipt={'graph':str(GRAPH),'parent_commit':base,'commit':commit,'source_and_checkpoint_bytes_verified':True,'training_steps':2000,'incumbent_step':report['incumbent_step'],'native_semantic_admission':'NOT_RUN','existing_programs_preserved':True};(run/'research-graph-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))

if __name__=='__main__':main()
