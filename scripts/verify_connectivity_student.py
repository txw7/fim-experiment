"""Exact-incidence metrics, raw head logits, and replay of saved checkpoints."""
import importlib.util,hashlib,json
from pathlib import Path
import torch

def main():
 root=Path(__file__).resolve().parents[1];run=Path((root/'working/connectivity-student/latest.txt').read_text().strip());report=json.loads((run/'report.json').read_text());spec=importlib.util.spec_from_file_location('recorded_connection_runner',run/'runner-source.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);torch.set_num_threads(2)
 for path,digest in report['pins'].items():
  if Path(path).resolve()!=Path(__file__).resolve():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest
 g=report['source_graph'];controls=json.loads((run/'controls.json').read_text());events=report['events']
 trained=next(e for e in events if e['kind']=='student_training_complete' and e['phase']=='before-feedback');feedback=next(e for e in events if e['kind']=='observer_start' and e['provider']=='qwen-feedback');assert trained['time_ns']<feedback['time_ns']
 def exact(metrics,graphs):
  tp=fp=fn=0
  for prediction,graph in zip(metrics['predictions'],graphs):
   expected={(graph['nodes'][e['source']]['id'],graph['nodes'][e['target']]['id'],e['role'],e['position'],e['depth'],e['relation']) for e in graph['edges']}
   predicted={(e['source'],e['target'],e['role'],e['position'],e['depth'],e['relation']) for e in prediction['predicted_edges']}
   tp+=len(expected&predicted);fp+=len(predicted-expected);fn+=len(expected-predicted)
  return {'tp':tp,'fp':fp,'fn':fn,'precision':tp/max(1,tp+fp),'recall':tp/max(1,tp+fn),'f1':2*tp/max(1,2*tp+fp+fn)}
 supplemental={}
 for name in ['incumbent','live']:
  net=m.Student();net.load_state_dict(torch.load(run/(name+'.pt'),weights_only=True));net.eval()
  source_metrics=m.evaluate(net,[g]);expected=report['source_candidate' if name=='incumbent' else 'live_source_candidate'];assert source_metrics==expected
  holdout=m.evaluate(net,controls['test']);out=net(g);raw=[]
  for e in g['edges']:
   a,b=e['source'],e['target'];raw.append({'source':g['nodes'][a]['id'],'target':g['nodes'][b]['id'],'expected_incidence':e,'raw_logits':{h:values[a,b].detach().tolist() for h,values in out.items()}})
  supplemental[name]={'source_exact_incidence':exact(source_metrics,[g]),'generated_exact_incidence':exact(holdout,controls['test']),'source_target_edge_logits':raw}
 report['exact_incidence_metrics']=supplemental;report['interior_training_order_verified']=True;report['structural_checks_passed']=4
 report['pins'][str(Path(__file__).resolve())]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
 m.save(run/'report.json',report);m.save(root/'working/text-primitives/connectivity-student.json',report)
 print(json.dumps({'run':str(run),'parameters':report['parameters'],'steps':report['steps'],'frozen_step':report['incumbent_step'],'generated_edge_f1':report['generated_holdout']['edge_f1'],'source_edge_f1':report['source_candidate']['edge_f1'],'exact_metrics':{k:{h:v for h,v in value.items() if h!='source_target_edge_logits'} for k,value in supplemental.items()},'teacher_checks':{name:(r if name=='qwen' else {h:a['choice'] for h,a in r['answers'].items()}) for name,r in report['observer_checks']['initial'].items()}}))

if __name__=='__main__':main()
