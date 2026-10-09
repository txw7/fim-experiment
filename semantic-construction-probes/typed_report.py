import json,sys,html,subprocess,hashlib
from pathlib import Path
import search as b
from common import sexp
root=Path(sys.argv[1]);results=json.loads((root/'results.json').read_text());rows=[];sections=[];native=[]
for name,d in results.items():
 ts=b.tokens(d['source']);textbyid={t['id']:t['text'] for t in ts}
 for stage in ('initial','repair'):
  z=d[stage]
  if z.get('status')!='COMPLETED':rows.append(f'| {name} | {stage} | {z["status"]} | — | — | — |');continue
  c=z['candidate'];v=z['checks'];rows.append(f'| {name} | {stage} | {len(v["errors"])} | {len(c["applications"])} | {len(c["networks"])} | {v["structural_gate"]} |')
  lisps=[]
  for a in c['applications']:
   args='\n'.join('    ('+p['role']+' : '+p['value_type']+'\n      '+p['filler']+')' for p in a['ports']);lisps.append('('+a['id']+'\n  ('+a['operator']+'\n'+args+')\n  (result\n    '+a['result_type']+')\n  (license\n    '+a['construction']+'))')
  sections.append('<details open><summary>'+name+' / '+stage+'</summary><pre>'+html.escape(d['source'])+'</pre><h3>Application projection</h3><pre>'+html.escape('\n\n'.join(lisps))+'</pre><h3>Exact typed objects and interfaces</h3><pre>'+html.escape(json.dumps(c,indent=2))+'</pre><h3>Checks</h3><pre>'+html.escape(json.dumps(v,indent=2))+'</pre><a href="'+name+'/'+stage+'/request.json">Exact request</a></details>')
  if not v['structural_gate']:continue
  objects=[{'id':t['id'],'kind':'occurrence','type':'lexical-occurrence','anchors':[t['id']],'members':[],'license':'literal'} for t in ts];rels=[]
  for a in c['applications']:
   objects.append({'id':a['id'],'kind':'operator','type':a['operator'],'anchors':a['anchors'],'members':[],'license':json.dumps({'law':a['construction'],'result_type':a['result_type']})})
   for p in a['ports']:
    objects.append({'id':p['id'],'kind':'port','type':p['value_type'],'anchors':a['anchors'],'members':[],'license':json.dumps({'role':p['role'],'owner':a['id']})})
    rels.append({'id':'edge-'+p['id'],'family':'argument','constitution':'unregistered-port-application','ends':[{'role':'application','target':a['id']},{'role':'port','target':p['id']},{'role':'filler','target':p['filler']}]})
  for p in c['positions']:objects.append({'id':p['id'],'kind':'position','type':p['value_type'],'anchors':[],'members':[],'license':p['license']})
  for n in c['networks']:objects.append({'id':n['id'],'kind':'network','type':'proposed-network','anchors':[],'members':n['members'],'license':json.dumps({'imports':n['imports'],'exports':n['exports']})})
  for r in c['relations']:rels.append({'id':r['id'],'family':r['family'],'constitution':r['license'],'ends':r['roles']})
  for x in c['bindings']:rels.append({'id':x['id'],'family':'binding','constitution':x['license'],'ends':[{'role':'binder','target':x['binder']},{'role':'position','target':x['position']},{'role':'domain','target':x['domain']}]})
  native.append({'id':stage,'source':name,'objects':objects,'relations':rels})
if native:
 (root/'native-input.sexp').write_text(sexp(native)+'\n')
 with (root/'native.log').open('w') as log:
  code=subprocess.run(['sbcl','--script',str(Path(__file__).with_name('native.lisp')),str(root/'native-input.sexp'),str(root/'native-output.sexp')],stdout=log,stderr=log,timeout=45).returncode
else:code=None
report='# Typed local construction probe\n\nSource lexical occurrences are held outside model output and remain unchanged. Models supply proposed applications, typed argument ports, licensed positions, bindings, recursive network membership and imports/exports. This defines a representation contract without supplying operator names or a preferred grammatical analysis.\n\n| Source | Stage | Structural errors | Applications | Networks | Structural gate |\n|---|---|---|---|---|---|\n'+'\n'.join(rows)+'\n\nNative storage adapter exit: '+str(code)+'. Native objects are opaque proposed meanings and unresolved incidence holes; this checks storage and region interior round trips, not grammatical law admission, entailment or correctness of model type labels.\n\nOnly declared source references, duplicate identities, argument interfaces, position/binding endpoints, network references and graph cycles are checked. Type names are model claims; their compatibility is not proved. Original grammatical ambiguity remains unresolved.\n'
(root/'report.md').write_text(report)
(root/'network.html').write_text('<!doctype html><meta charset="utf-8"><title>Typed local construction evidence</title><style>body{font:16px system-ui;background:#14212b;color:#eee;margin:30px}pre{white-space:pre-wrap;background:#20313e;padding:15px}details{border:1px solid #537285;padding:14px;margin:15px 0}summary{cursor:pointer}a{color:#8cdaff}</style><h1>Typed grammatical construction proposals</h1><p>Semantic laws unregistered; no native semantic admission.</p><a href="report.md">Results and native storage check</a>'+''.join(sections))
(root/'manifest.json').write_text(json.dumps({str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file() and p.name!='manifest.json'},indent=2)+'\n');print(report)
