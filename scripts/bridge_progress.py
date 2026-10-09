"""Project durable running receipts into the existing viewer without claiming completion."""
import json,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];run=Path((ROOT/'working/philosophy-spec-bridge/active.txt').read_text().strip())
read=lambda p:json.loads(p.read_text());events=[json.loads(x) for x in (run/'events.jsonl').read_text().splitlines()];calls=dict(collections.Counter(e['provider'] for e in events if e['kind']=='observer_complete'));steps={n:max([e['step'] for e in events if e['kind']=='student_training_complete' and e['provider']==n] or [0]) for n in ['symbolic','probabilistic']};units=read(run/'source-units.json');schema=read(run/'feature-schema.json');observations={}
for row in units:
 ident=row['id'];observations[ident]={'jev':{'answers':{}},'laya':{'windows':[]}}
 for p in (run/ident).glob('layer-*/jev/response.json'):observations[ident]['jev']['answers'].update(read(p)['answers'])
 for p in sorted((run/ident).glob('layer-*/window-*/laya/response.json')):
  ix=int(p.parts[-3].split('-')[-1]);windows=observations[ident]['laya']['windows']
  while len(windows)<=ix:windows.append({'answers':{}})
  windows[ix]['answers'].update(read(p)['answers'])
stages=read(run/'stages.json') if (run/'stages.json').exists() else [];r={'schema':'BridgeRunningReceipt','status':'RUNNING','run':str(run),'units':units,'feature_schema':schema,'feature_dimensions':len(schema),'features':read(sorted(run.glob('features-layer-*.json'))[-1]),'source_graph':read(run/'source-graph.json'),'observations':observations,'neural':read(run/'neural/features.json'),'stages':stages,'new_students':{n:{'steps':v,'state':'RUNNING; no completed evaluation yet'} for n,v in steps.items()},'fresh_calls':calls,'coverage':{'lexical':'EXECUTED all six units, including connected grams/morphology/parser/keywords/TAACO/graph kernel','neural':'EXECUTED six frozen backbones and eight original classifier heads','tower':'RUNNING; events count actual completed requests only','student':'Counts above are completed interior update blocks only'},'pins':{},'limits':['RUNNING snapshot. No completion or semantic admission claimed.']};(ROOT/'working/text-primitives/philosophy-spec-bridge-progress.json').write_text(json.dumps(r)+'\n')
print('Published RUNNING viewer snapshot',calls,steps)
