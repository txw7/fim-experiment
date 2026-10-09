"""Verify real updates between prompts, masks, original weights and source lineage."""
import hashlib,json
from pathlib import Path
from collections import Counter
from philosophy_spec_bridge import ROOT,GROUPS,HEADS

def main():
 run=Path((ROOT/'working/philosophy-spec-bridge/latest.txt').read_text().strip());r=json.loads((run/'report.json').read_text());events=r['events'];checks=[]
 assert len(HEADS)==26 and list(map(len,GROUPS))==[8,11,7];checks.append('original 26 logic heads retained')
 for name,s in r['new_students'].items():
  assert s['steps']==1500 and [x['step'] for x in s['history']]==[250,500,750,1000,1250,1500];checks.append(name+' actual 1500 interior updates')
 for layer in [1,2,3]:
  initial=max((e for e in events if e['kind']=='observer_complete' and e['provider']=='qwen' and e['phase']==f'layer-{layer}/initial'),key=lambda e:e['time_ns'])
  feedback=next(e for e in events if e['kind']=='observer_start' and e['provider']=='qwen-feedback' and e['phase']==f'layer-{layer}/feedback')
  trained=[e for e in events if e['kind']=='student_training_complete' and e['phase']==f'layer-{layer}/before-feedback'];assert len(trained)==2 and all(initial['time_ns']<e['time_ns']<feedback['time_ns'] for e in trained)
 checks.append('both students updated between initial and feedback prompts in all three layers')
 source=(run/'source.txt').read_text();assert hashlib.sha256((run/'source.txt').read_bytes()).hexdigest()==r['source_sha256']
 for u in r['units']:assert source[u['source_ref']['start']:u['source_ref']['end']]==u['text']
 checks.append('all six source spans exact')
 for name,o in r['original_student_models'].items():assert hashlib.sha256((run/('origin-'+name+'.pt')).read_bytes()).hexdigest()==o['snapshot_sha256']
 checks.append('immutable philosophy origin snapshots match fork provenance; live originals may advance externally')
 assert len(r['neural']['classifiers'])==8
 for c in r['neural']['classifiers'].values():assert len(c['raw_logits'])==len(c['scores'])==5
 checks.append('eight original classifier heads have actual logits on five fresh spec pairs')
 schemas=r['feature_schema'];assert len(schemas)==len(set(schemas))==r['feature_dimensions']
 for f in r['features'].values():assert len(f['values'])==len(f['masks'])==len(schemas) and all(v in [0,1] for v in f['masks'])
 last=r['features']['s3-p5'];assert all(last['masks'][i]==0 for i,k in enumerate(schemas) if k.startswith(('classifier:','backbone:')))
 checks.append('absent last-paragraph pair masked rather than fabricated')
 for f in r['features'].values():
  assert all(f['masks'][i]==1 for i,k in enumerate(schemas) if k.startswith('jev:profile:S-2:'))
  assert all(f['masks'][i]==0 for i,k in enumerate(schemas) if k.startswith(('jev:profile:S-1:truth:','jev:profile:S-1:falsity:')))
 checks.append('native score legend correctly projected; inapplicable distinctions masked')
 assert r['checkpoint_replay_verified'];checks.append('saved frozen checkpoint replay verified')
 out={'status':'PASS','checks':checks,'source_semantic_admission':'NOT_RUN','single_source_pilot':True};(run/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
if __name__=='__main__':main()
