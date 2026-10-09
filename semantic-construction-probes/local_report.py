import json,html,hashlib,sys,importlib.util
from pathlib import Path
def svg(c):
 pos={o['id']:(100+i%5*220,75+i//5*105) for i,o in enumerate(c['objects'])}
 y=100+(len(c['objects'])+4)//5*105
 pos.update({r['id']:(100+i%5*220,y+i//5*70) for i,r in enumerate(c['relations'])})
 out=[f'<svg viewBox="0 0 1100 {y+(len(c["relations"])+4)//5*70+60}">']
 for rel in c['relations']:
  x,y0=pos[rel['id']]
  for e in rel['ends']:
   if e['target'] in pos:
    a,b=pos[e['target']];out.append(f'<line x1="{x}" y1="{y0}" x2="{a}" y2="{b}"/><text x="{(x+a)/2}" y="{(y0+b)/2}">{html.escape(e["role"])}</text>')
 for o in c['objects']:
  x,y0=pos[o['id']];color='#417350' if o['kind']=='network' else '#315f80'
  out.append(f'<rect x="{x-95}" y="{y0-22}" width="190" height="45" rx="8" fill="{color}"/><text x="{x-90}" y="{y0-5}">{html.escape(o["id"]+" "+o["kind"])}</text><text x="{x-90}" y="{y0+10}">{html.escape(o["type"][:27])}</text>')
 for rel in c['relations']:
  x,y0=pos[rel['id']];out.append(f'<rect x="{x-80}" y="{y0-16}" width="160" height="32" rx="7" fill="#835f36"/><text x="{x-75}" y="{y0+4}">{html.escape(rel["id"]+" "+rel["family"])}</text>')
 return ''.join(out)+'</svg>'


r=Path(sys.argv[1]);results=json.loads((r/'results.json').read_text());rows=[];body=[]
for name,d in results.items():
 state={'source':d['source'],'alternatives':{k:v['candidate'] for k,v in d.items() if k in ('initial','repair') and v.get('status')=='COMPLETED'}}
 if state['alternatives']:
  spec=importlib.util.spec_from_file_location('jev','/home/user0/research-gold-disrpt/corpusGraph/scripts/jev_systemone.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  q={'fit':{'type':'choice','instructions':'Which exact grammatical graph best preserves source operators, argument positions, bindings and unresolved attachment? Reject missing source structure. This is support, not native proof.','criteria':{**{k:k+' exact graph' for k in state['alternatives']},'neither':'Both unsupported or malformed.','unresolved':'Cannot distinguish.'}}}
  (r/name/'jev-request.json').write_text(json.dumps({'state':state,'questions':q},indent=2)+'\n')
  try:resp=m.decide(json.dumps(state),q)
  except Exception as ex:resp={'error':str(ex)}
  (r/name/'jev-response.json').write_text(json.dumps(resp,indent=2)+'\n')
 for stage in ('initial','repair'):
  v=d[stage]
  if v.get('status')!='COMPLETED':rows.append(f'| {name} | {stage} | {v.get("status")} | — | — | — |');continue
  c=v['candidate'];ch=v['checks'];rows.append(f'| {name} | {stage} | {len(ch["errors"])} | {ch["source_preserved"]} | {ch["complete_operator_coverage"]} | {ch["metrics"]["networks"]} |')
  body.append('<details><summary>'+name+' / '+stage+'</summary><pre>'+html.escape(d['source'])+'</pre><h3>Graph proposal</h3>'+svg(c)+'<pre>'+html.escape(json.dumps(c,indent=2))+'</pre><h3>Checks</h3><pre>'+html.escape(json.dumps(ch,indent=2))+'</pre><a href="'+name+'/'+stage+'/request.json">Exact prompt</a></details>')
report='# Local construction and preservation probe\n\nEach input has an immutable lexical substrate. Model candidates must reproduce it unchanged; derived objects reference exact source occurrences. Copying lexical tokens does not count as interpreting an operator. Source operators without a derived anchor or incidence remain explicitly uninterpreted.\n\n| Input | Stage | Structural errors | Source unchanged | Operator covered | Networks |\n|---|---|---|---|---|---|\n'+'\n'.join(rows)+'\n\nCoverage establishes reference presence only, not correct grammatical interpretation. Construction licenses remain proposed, not native laws. Composition runs only if all three repaired proposals pass structural, source-preservation and operator-coverage checks, and remains a hypothesis.\n\nComposition: '+json.dumps(json.loads((r/'composition.json').read_text()),indent=2)+'\n'
(r/'report.md').write_text(report)
(r/'network.html').write_text('<!doctype html><meta charset="utf-8"><title>Local construction evidence</title><style>body{font:16px system-ui;background:#14212b;color:#eee;margin:30px}pre{white-space:pre-wrap;background:#20313e;padding:15px}details{border:1px solid #537285;padding:14px;margin:15px 0}summary{cursor:pointer}svg{width:100%;background:#20313e}text{fill:#eee;font:11px system-ui}line{stroke:#7298ad}a{color:#8cdaff}</style><h1>Immutable source → grammatical candidates → repair</h1><p>Semantic admission not run.</p><a href="report.md">Results and composition gate</a>'+''.join(body))
(r/'manifest.json').write_text(json.dumps({str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in r.rglob('*') if p.is_file() and p.name!='manifest.json'},indent=2)+'\n');print(report)
