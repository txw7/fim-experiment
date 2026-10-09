import json,hashlib,html,sys
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

r=Path(sys.argv[1]);rows=[];sections=[]
for p in sorted(r.iterdir()):
 if not p.is_dir() or not (p/'candidates.json').exists():continue
 candidates=json.loads((p/'candidates.json').read_text());checks=json.loads((p/'checks.json').read_text());source=json.loads((p/'source.json').read_text())
 for c in candidates:
  v=checks[c['id']];m=v['metrics'];rows.append(f"| {p.name} | {c['id']} | {len(c['objects'])}/{len(c['relations'])} | {len(v['errors'])} | {len(v['occurrence_diagnostics'])} | {m['networks']} | {m['network_operands']} | {m['relation_operands']} |")
  sections.append('<details><summary>'+html.escape(p.name+' / '+c['id'])+'</summary><h3>Unchanged source</h3><pre>'+html.escape(source['text'])+'</pre><h3>Candidate network</h3>'+svg(c)+'<h3>Diagnostics</h3><pre>'+html.escape(json.dumps(v,indent=2))+'</pre><h3>Exact graph</h3><pre>'+html.escape(json.dumps(c,indent=2))+'</pre><p><a href="'+p.name+'/'+c['id'].split('-')[1]+'/'+c['id'].split('-')[0]+'/request.json">Exact prompt/request</a></p></details>')
report='# Expanded construction probe\n\nThree unchanged source inputs. Two independent sampled initial proposals per input, each with a paired feedback repair. Limits increased from 8 objects/5 relations/1,300 completion tokens to 40 objects/48 relations/6,500 tokens. These are diagnostics, not an accuracy benchmark: no gold graph or semantic-law admission.\n\n| Source | Candidate | Objects/relations | Structural errors | Occurrence warnings | Networks | Network operands | Relation operands |\n|---|---|---|---|---|---|---|---|\n'+'\n'.join(rows)+'\n\nA network count alone does not establish semantic synthesis. All proposed operator and relation meanings still require native validation. Laya classifications are accepted only when the service reports no dropped state or truncated questions. Independent proposals use temperature 0.55 with distinct seeds; their independence is procedural, not statistical.\n'
(r/'report.md').write_text(report)
(r/'network.html').write_text('<!doctype html><meta charset="utf-8"><title>Expanded semantic construction</title><style>body{background:#121c26;color:#eee;font:16px system-ui;margin:30px}pre{white-space:pre-wrap;background:#1d2a37;padding:18px}details{margin:20px 0;border:1px solid #526779;padding:12px}summary{cursor:pointer}a{color:#8edcff}svg{width:100%;background:#1d2a37}text{fill:#eee;font:11px system-ui}line{stroke:#7997ab}</style><h1>Expanded construction evidence</h1><p>Hypotheses; semantic admission NOT RUN. Relations are graph objects, not only edges.</p><a href="report.md">Comparison table</a>'+''.join(sections))
(r/'manifest.json').write_text(json.dumps({str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in r.rglob('*') if p.is_file() and p.name!='manifest.json'},indent=2)+'\n')
print(report)
