"""Read actual saved live/frozen forks on every unit, with and without observed features."""
import json,torch
from pathlib import Path
from philosophy_spec_bridge import ROOT,BridgeStudent,HEADS,CHOICES
run=Path((ROOT/'working/philosophy-spec-bridge/latest.txt').read_text().strip());r=json.loads((run/'report.json').read_text());rows=r['units'];values=torch.tensor([r['features'][u['id']]['values'] for u in rows]);masks=torch.tensor([r['features'][u['id']]['masks'] for u in rows]);out={}
torch.set_num_threads(2)
for name in ['symbolic','probabilistic']:
 c=torch.load(run/(name+'-bridge.pt'),weights_only=False);out[name]={}
 for branch in ['live','frozen']:
  model=BridgeStudent(r['feature_dimensions']);model.load_state_dict(c[branch]);model.eval();out[name][branch]={}
  for mode in ['conditioned','all_features_masked']:
   with torch.no_grad():logits=model(rows,values,masks if mode=='conditioned' else masks*0)
   result=[]
   for unit,x in zip(rows,logits):
    heads={h:{'raw_logits':v.tolist(),'categorical_readout':dict(zip(CHOICES,v.softmax(-1).tolist())),'p_yes':float(torch.sigmoid(v[0]-v[1])) if name=='probabilistic' else None,'interpretation':'Independent Bernoulli p_yes; unresolved/categorical readout is diagnostic and uncalibrated' if name=='probabilistic' else 'Qwen pseudo-label distribution; uncalibrated'} for h,v in zip(HEADS,x)}
    result.append({'source_id':unit['id'],'heads':heads})
   out[name][branch][mode]=result
metrics={}
for name,branches in out.items():
 metrics[name]={}
 for branch,modes in branches.items():
  metrics[name][branch]={}
  for mode,records in modes.items():
   record=next(x for x in records if x['source_id']=='s3-p5');pred=record['heads'];targets={h:v for stage in r['stages'] for h,v in stage['feedback']['profiles']['s3-p5'].items()}
   if name=='symbolic':
    agreement=sum(max(pred[h]['categorical_readout'],key=pred[h]['categorical_readout'].get)==targets[h] for h in HEADS);metrics[name][branch][mode]={'teacher_label_agreement':agreement/len(HEADS),'matched':agreement,'heads':len(HEADS),'always_absent_baseline':sum(v=='absent' for v in targets.values())/len(HEADS),'authority':'Agreement with Qwen pseudo-labels, not gold accuracy'}
   else:
    target={h:r['observations']['s3-p5']['jev']['answers']['logic:'+h]['noul'] for h in HEADS};metrics[name][branch][mode]={'distillation_probability_mse':sum((pred[h]['p_yes']-target[h])**2 for h in HEADS)/len(HEADS),'authority':'Distance to native Jev observations; not calibration against truth'}
(run/'student-metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
(run/'all-student-logits.json').write_text(json.dumps(out,indent=2)+'\n');print('Saved 2 students × 2 branches × 2 feature modes × 6 units × 26 heads')
