"""Verify saved training evidence and deterministic checkpoint inference."""
import importlib.util,json,hashlib
from pathlib import Path
import torch

def main():
 root=Path(__file__).resolve().parents[1];run=Path((root/'working/fresh-s3-tower/latest.txt').read_text().strip())
 spec=importlib.util.spec_from_file_location('recorded_fresh_runner',run/'runner-source.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 report=json.loads((run/'report.json').read_text());source=(run/'source.txt').read_text();torch.set_num_threads(2)
 assert report['retained_responses_used']==0 and report['weights_changed'] and report['training_steps']==2000
 for row in report['records']:
  assert source[row['char_start']:row['char_end']]==row['text'];m.validate(row['graph']['proposal'],row['text'])
 history=report['history'];assert len(history)==8
 assert all(x['step_after']-x['step_before']==250 for x in history)
 assert [x['step_before'] for x in history]==list(range(0,2000,250))
 train={r['id'] for r in report['records'] if r['split']=='train'}
 assert {r['record'] for r in history}==train
 for ident in train:
  events=[e for e in report['events'] if e.get('record')==ident]
  trained=next(e for e in events if e['kind']=='student_training_complete' and e['phase']=='before-feedback')
  reviewed=next(e for e in events if e['kind']=='observer_start' and e['provider']=='qwen-feedback')
  assert trained['time_ns']<reviewed['time_ns']
 rows=json.loads((run/'evaluation-records.json').read_text());test=[r for r in rows if r['split']=='test']
 metrics={}
 initial=torch.load(run/'initial.pt',weights_only=False);initial_net=m.Tiny(initial['vocab']);initial_net.load_state_dict(initial['state_dict'])
 actual_hash=hashlib.sha256(b''.join(p.detach().numpy().tobytes() for p in initial_net.parameters())).hexdigest();assert actual_hash==report['initial_weights_sha256']
 actual_baseline=m.score(initial_net,[r for r in rows if r['split']=='validation'])
 if report.get('resume_events'):
  (run/'pre-replay-report.json').write_text(json.dumps(report,indent=2)+'\n')
  report['validation_baseline']=actual_baseline;report['baseline_replayed_from_initial_checkpoint']=True
  report['evidence_limitations']=['Two rejected-attempt Laya/Jev response files were replaced by fresh continuation calls; their event counts remain. Accepted training inputs and all Qwen attempt responses are retained.','Continuation reset optimizer at step 1000.']
  (run/'report.json').write_text(json.dumps(report,indent=2)+'\n');m.save(root/'working/text-primitives/fresh-s3-tower.json',report)
 for name in ('live','incumbent'):
  checkpoint=torch.load(run/(name+'.pt'),weights_only=False,map_location='cpu');net=m.Tiny(checkpoint['vocab']);net.load_state_dict(checkpoint['state_dict'])
  metrics[name]={'step':checkpoint['step'],'combined':m.score(net,test),'source_only':m.score(net,test,mask_observers=True,mask_graph=True)}
 for p,expected in zip(metrics['incumbent']['combined']['predictions'],report['test']['predictions']):
  for h in m.HEADS:assert torch.allclose(torch.tensor(p['heads'][h]['raw_logits']),torch.tensor(expected['heads'][h]['raw_logits']),atol=1e-6,rtol=1e-6)
 result={'source_spans_verified':True,'eight_training_phases_verified':True,'interior_order_verified':True,'checkpoint_replay_matches':True,'live_and_incumbent':metrics,'limits':'combined input contains teacher answers; source-only holdout is the independent-input diagnostic, targets remain pseudo-labels'}
 (run/'checkpoint-replay.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='live_and_incumbent'}))

if __name__=='__main__':main()
