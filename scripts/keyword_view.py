"""Build the single four-corpus results graph and evidence viewer."""
import collections,hashlib,json,math,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'working/text-primitives'
def rows(name):
 text=(ROOT/name).read_text()
 try:
  value=json.loads(text)
  if isinstance(value,list): return value
 except json.JSONDecodeError: pass
 return [json.loads(line) for line in text.splitlines() if line]
def read(name):return json.loads((ROOT/name).read_text())
FAM=['me','plato','parmenides','aristotle'];LABEL={'me':'Your essay','plato':'Plato','parmenides':'Parmenides','aristotle':'Aristotle'}
sources=rows('sources.jsonl');byid={x['id']:x for x in sources};tokens={d['id']:[m.group().casefold() for m in re.finditer(r"[^\W\d_]+(?:['’][^\W\d_]+)?",d['text'])] for d in sources}
terms={x['term']:x for x in rows('terms.jsonl')};disp={x['term']:x for x in rows('dispersion.jsonl')};docs={x['source_id']:x for x in rows('document-metrics.jsonl')};extended=read('extended-metrics.json');network=read('keyword-network.json');latent=read('transformer-latent-index.json');latentrows=rows('transformer-latent-rows.json');conceptnet=read('transformer-concept-network.json');local=read('local-model-observations.json')
assoc=rows('association.jsonl');assoc=sorted(assoc,key=lambda x:(x['npmi'],x['count']),reverse=True)[:90];wanted={tuple(sorted(x['terms'])) for x in assoc};by_pair=collections.defaultdict(collections.Counter)
for d in sources:
 ts=tokens[d['id']]
 for i,a in enumerate(ts):
  for b in ts[i+1:i+6]:
   pair=tuple(sorted((a,b)))
   if pair in wanted:by_pair[pair][d['family']]+=1
familystats={}
for f in FAM:
 selected=[d for d in sources if d['family']==f];dm=[docs[d['id']] for d in selected];sur=[x for x in rows('count-surprisal.jsonl') if byid[x['source_id']]['family']==f]
 counts=collections.Counter()
 for d in selected:counts.update(tokens[d['id']])
 fam=extended['distributions'][f];bleu=extended['self_bleu'][f]
 familystats[f]={'label':LABEL[f],'documents':len(selected),'tokens':sum(len(tokens[d['id']]) for d in selected),'types':len(counts),'entropy_bits':fam['entropy_bits'],
  'mean_ttr':sum(x['ttr'] for x in dm)/len(dm),'mean_rttr':sum(x['rttr'] for x in dm)/len(dm),'mean_cttr':sum(x['cttr'] for x in dm)/len(dm),'mean_zlib_ratio':sum(x['zlib_ratio'] for x in dm)/len(dm),
  'self_bleu':bleu['mean'],'heldout_count_model_cross_entropy':sum(x['cross_entropy_bits'] for x in sur if x['cross_entropy_bits'] is not None)/sum(x['cross_entropy_bits'] is not None for x in sur) if any(x['cross_entropy_bits'] is not None for x in sur) else None,'heldout_count_model_units':len(sur),
  'mean_heldout_perplexity':sum(x['perplexity'] for x in sur if x['perplexity'] is not None)/sum(x['perplexity'] is not None for x in sur) if any(x['perplexity'] is not None for x in sur) else None}
graphstop=set('the of is to in a be that it for as if from but by what with they we there this have an would then can at no some into when has more do on he its does another which than are was were'.split())
gramnet={};
for n in (1,2,3):
 nc=collections.Counter();ec=collections.Counter();nf=collections.defaultdict(collections.Counter);ef=collections.defaultdict(collections.Counter);ex=collections.defaultdict(list)
 for d in sources:
  ts=tokens[d['id']];f=d['family']
  for i in range(len(ts)-n+1):
   g=' '.join(ts[i:i+n]);nc[g]+=1;nf[g][f]+=1
  for i in range(len(ts)-n):
   a=' '.join(ts[i:i+n]);b=' '.join(ts[i+1:i+n+1]);ec[a,b]+=1;ef[a,b][f]+=1
   if len(ex[a,b])<4 and d['id'] not in ex[a,b]:ex[a,b].append(d['id'])
 nodes=[g for g,c in nc.most_common(90) if not all(w in graphstop for w in g.split())]
 for g in ['truth','false','being','one','all','things','not','and','or','is true','all things','being one','the truth','truth is','is true that','all are false','all things are']:
  if len(g.split())==n and nc[g] and g not in nodes:nodes.append(g)
 allowed=set(nodes);candidate=[(a,b,c) for (a,b),c in ec.items() if a in allowed and b in allowed];keep=set()
 for g in allowed:
  keep.update((a,b) for a,b,c in sorted((e for e in candidate if g in e[:2]),key=lambda e:e[2],reverse=True)[:3])
 gramnet[str(n)]={'nodes':[{'id':g,'count':nc[g],'families':{f:nf[g][f] for f in FAM}} for g in nodes],
   'edges':[{'source':a,'target':b,'count':c,'families':{f:ef[a,b][f] for f in FAM},'sources':ex[a,b]} for a,b,c in candidate if (a,b) in keep]}
assocout=[]
for x in assoc:
 key=tuple(sorted(x['terms']));assocout.append({**x,'families':{f:by_pair[key][f] for f in FAM}})
shown=sorted([n for n in network['nodes'] if n['id'] not in graphstop],key=lambda x:x['pagerank'],reverse=True)[:60];ids={n['id'] for n in shown};edges=[e for e in network['edges'] if e['source'] in ids and e['target'] in ids]
keep=set()
for n in ids:keep.update((e['source'],e['target']) for e in sorted((q for q in edges if n in (q['source'],q['target'])),key=lambda q:q['count'],reverse=True)[:2])
edges=[e for e in edges if (e['source'],e['target']) in keep]
prefix={'me':'essay:','plato':'plato:','parmenides':'parmenides:','aristotle':'source-unit:archelogos:'}
for e in edges:e['families']={f:sum(v for sid,v in e.get('source_units',{}).items() if sid.startswith(prefix[f])) for f in FAM}
coverage=[
 ('Unigrams, bigrams, trigrams; connected 1/2/3-gram graphs','Computed on 7,723 units; links weighted by adjacent n+1-grams.'),
 ('Co-occurrence, PMI, PPMI, NPMI, lift, confidence, conviction, LogDice, LLR','Computed in five-token windows. LLR is descriptive; overlapping windows do not meet an independent-trial significance model.'),
 ('TF-IDF, Zipf rank/frequency, empirical vocabulary growth','Computed. Growth follows source-file order; no time or saturation claim.'),
 ('Hypergeometric lexical specificity, family dispersion, interword gap mean/SD, term entropy','Computed; specificity p-values are unadjusted and conditioned on corpus margins.'),
 ('Token entropy, adjacent conditional entropy/MI, smoothed KL/JS','Computed. KL/JS use alpha=.5.'),
 ('Cross-entropy, perplexity, token surprisal','Computed with a held-out smoothed unigram model, not a neural language model.'),
 ('TTR, RTTR, CTTR, zlib compression, Self-BLEU','Computed; Self-BLEU uses fixed-seed samples of at most 32 units/family.'),
 ('Keyword graph degree, weighted degree, PageRank, clustering, components, path length','Computed. Path mean samples 64 fixed-seed origins; graph is undirected and count-weighted.'),
 ('Transformer MiniLM vectors, cosine kNN, concept-token cosine, PCA, k-means','Computed locally on CPU for every source unit. Similarity is not identity, entailment or proof.'),
 ('Tiny student head logits','Raw incumbent and live logits for ten explicit-operator classes on every unit; model is experimental and trained from seven unique records.'),
 ('Local Laya/Qwen outputs','Prior source-pinned run retained: Laya probability distributions; Qwen raw completions. Qwen token logprobs were not recorded.'),
 ('Small-world/power-law tests, graph kernels','Tools are available but these properties were not tested/fitted.'),
 ('Stemming / lemmatization','Snowball stems computed separately; lemmatization not run.'),
 ('Diachronic semantic change / sense distributions','Not estimable: sources have no aligned time slices or sense annotations; authors/translation families are not a time axis.'),
 ('WID from neural surprisal; Qwen token logits','Unavailable in these retained runs. The unigram count surprisal and student classification logits are different quantities.'),
 ('Morphology MDL, syntax/dependency/Yngve/T-units, TAACO cohesion','Acquired tools or smoke runs exist; no complete four-corpus results are claimed here.'),
 ('Qualia/inheritance, semantic compound overlap, Katz gamma, AMR grounding','Requires a licensed ontology/operational definition or model outputs not present in this corpus run.')]
payload={'families':familystats,'probes':[{ 'term':t,'count':terms.get(t,{}).get('count',0),'families':{f:disp.get(t,{}).get('family_counts',{}).get(f,0) for f in FAM}} for t in ['truth','false','falseness','being','one','substance','form','all','things','and','or','not']],
 'associations':assocout,'network':{'nodes':shown,'edges':edges,'all_nodes':len(network['nodes']),'all_edges':len(network['edges'])},'gram_networks':gramnet,
 'graph_metrics':extended['graph'],'comparisons':extended['family_comparisons'],'count_model':{k:extended['count_model'][k] for k in ['model','alpha','split','heldout_source_ids']},
 'vocabulary_growth':extended['vocabulary_growth'],'self_bleu':extended['self_bleu'],'coverage':[{'measure':a,'status':b} for a,b in coverage],
 'transformer':latent,'latent_points':[{'source_id':r['source_id'],'family':r['family'],'cluster':r['cluster'],'pca2':r['pca2'],'neighbors':r['neighbors'][:3],'keywords':r['keyword_cosines'],'student_logits':r['student_logits'],'text':byid[r['source_id']]['text'][:320]} for r in latentrows],
 'concept_network':conceptnet,'concept_nearest':latent['concept_nearest_source_units'],'local_models':local,
 'sources_manifest_sha256':hashlib.sha256((ROOT/'manifest.json').read_bytes()).hexdigest()}
page=r'''<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Philosopher Results Graph</title><style>
:root{color-scheme:dark;--bg:#10151f;--panel:#192231;--line:#334155;--text:#edf2fa;--muted:#aab7c8;--cyan:#67d4e8;--gold:#f1c878;--essay:#edaa59;--plato:#67d4e8;--parmenides:#b69aff;--aristotle:#8fd28f}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:15px/1.5 system-ui,sans-serif}header{padding:20px clamp(16px,4vw,52px);background:#141c29;border-bottom:1px solid var(--line)}h1{margin:0;font-size:26px}h2{font-size:19px;margin:0 0 8px}h3{font-size:16px;margin:0 0 8px}p{margin:5px 0;color:var(--muted)}main{max-width:1480px;margin:auto;padding:20px clamp(12px,3vw,40px) 48px}.controls{display:flex;gap:14px;flex-wrap:wrap;align-items:center;margin:12px 0}select{background:#202d40;color:white;border:1px solid #596b82;padding:8px 11px;border-radius:7px;font:inherit}.panel,.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px;margin-bottom:14px;min-width:0}.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}.cards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.metric{font-size:24px;color:var(--cyan);font-variant-numeric:tabular-nums}.small{font-size:12px;color:var(--muted)}.tablewrap{overflow:auto;max-height:570px}table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}th,td{text-align:right;border-bottom:1px solid var(--line);padding:7px 8px;white-space:nowrap}th:first-child,td:first-child{text-align:left}th{color:var(--muted);position:sticky;top:0;background:var(--panel);z-index:1}td.text{text-align:left;white-space:normal;min-width:190px}.badge{display:inline-block;background:#25354a;padding:2px 7px;border-radius:999px;margin:2px;font-size:11px}svg{width:100%;height:570px;background:#131c29;border-radius:8px}svg line{stroke:#8494aa;opacity:.52}svg circle{stroke:#d8f4fa;stroke-width:.5;cursor:pointer}svg text{fill:#e6edf6;font-size:11px;pointer-events:none}details{margin-top:8px}summary{cursor:pointer;color:var(--cyan)}.detail{min-height:54px;padding:8px 0;color:#d8e1ed;white-space:pre-wrap}.legend{display:flex;gap:14px;flex-wrap:wrap}.dot{display:inline-block;width:11px;height:11px;border-radius:50%;margin-right:5px}article{min-width:0}.nowrap{white-space:nowrap}.muted{color:var(--muted)}@media(max-width:900px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}.cards{grid-template-columns:1fr}svg{height:460px}}@media(max-width:520px){.grid{grid-template-columns:1fr}.controls{align-items:flex-start;flex-direction:column}}
</style><header><h1>Your essay · Plato · Parmenides · Aristotle</h1><p>One results graph: count structure, network topology, transformer similarity, and local model evidence. Source units stay pinned; model scores remain fallible observations.</p></header><main><div class="controls"><label>Corpus slice <select id="family"><option value="all">All four</option><option value="me">Your essay</option><option value="plato">Plato</option><option value="parmenides">Parmenides</option><option value="aristotle">Aristotle</option></select></label><span id="sourcePin" class="small"></span></div>
<section class="panel"><h2>Corpus profiles</h2><div id="profiles" class="grid"></div><p class="small">TTR, RTTR, CTTR, zlib ratio and held-out count-model surprisal are per-unit averages. Corpus size, editing and segmentation differ.</p></section>
<section class="panel"><h2>Logical and concept unigrams</h2><div class="tablewrap"><table><thead><tr><th>1-gram</th><th>Total count</th><th>Your essay</th><th>Plato</th><th>Parmenides</th><th>Aristotle</th></tr></thead><tbody id="probes"></tbody></table></div></section>
<section class="panel"><h2>Associations · weighted five-token windows</h2><p>Direction-bearing rule-association scores describe token events; they do not assert implication or proof. Filtered corpus slices show the event counts by family while association scores are pooled across all four.</p><div class="tablewrap"><table><thead><tr><th>Pair</th><th>Count</th><th>PMI</th><th>PPMI</th><th>NPMI</th><th>Lift</th><th>Confidence</th><th>Conviction</th><th>LogDice</th><th>LLR</th><th>Family events</th></tr></thead><tbody id="associations"></tbody></table></div></section>
<section class="panel"><h2>Keyword co-occurrence network</h2><p id="networkMeta"></p><svg id="wordGraph" viewBox="0 0 1200 570" aria-label="Keyword co-occurrence graph"></svg><div id="wordDetail" class="detail">Select a word node to see weighted links.</div></section>
<section class="panel"><h2>Connected n-gram networks</h2><p>Every edge advances one token. 1-gram→1-gram edges are bigrams; 2-gram edges count trigrams; 3-gram edges count four-grams. No edge crosses a source-unit boundary.</p><div class="controls"><label>Node size <select id="gramSize"><option value="1">1-gram nodes / bigram links</option><option value="2">2-gram nodes / trigram links</option><option value="3">3-gram nodes / four-gram links</option></select></label></div><p id="gramMeta" class="small"></p><svg id="gramGraph" viewBox="0 0 1200 570" aria-label="Connected n-gram graph"></svg><div id="gramDetail" class="detail">Select a gram node to inspect its continuation and source IDs.</div></section>
<section class="panel"><h2>Transformer latent map · all source units</h2><p>MiniLM-L6-v2 sentence vectors, cosine neighbors, 12-cluster k-means and a PCA projection. Click a point to inspect its nearest passages, concept-token cosine scores and raw tiny-student operator logits.</p><div id="latentMeta" class="small"></div><div id="legend" class="legend"></div><svg id="latentGraph" viewBox="0 0 1200 570" aria-label="Transformer latent projection"></svg><div id="latentDetail" class="detail">Select a passage point.</div><details><summary>Family centroid cosine comparisons</summary><div id="centroidTable" class="tablewrap"></div></details></section>
<section class="panel"><h2>Concept token ↔ keyword cosine network</h2><p>Edges are MiniLM cosine similarity between isolated keyword strings. They show model-space proximity; they do not mean the terms are identical or interchangeable.</p><p id="conceptMeta" class="small"></p><svg id="conceptGraph" viewBox="0 0 1200 570" aria-label="Concept token cosine graph"></svg><div id="conceptDetail" class="detail">Select a concept to see nearest source units in each corpus.</div></section>
<section class="panel"><h2>Local model evidence</h2><p>Student outputs are raw 10-head operator logits from the two existing local checkpoints. Laya returned categorical probabilities. Qwen returned raw completion text; those requests did not retain token logprobs.</p><div id="modelMeta" class="grid"></div><details><summary>Prior Laya/Qwen philosopher runs · prompt modes and per-head score distributions</summary><div id="teacherRows" class="tablewrap"></div></details></section>
<section class="panel"><h2>Measures you listed · computed state</h2><div id="coverage" class="tablewrap"></div></section>
<section class="panel"><h2>Corpus comparisons and graph diagnostics</h2><div class="cards"><article class="card"><h3>Smoothed lexical KL / JS</h3><div id="compareRows" class="tablewrap"></div></article><article class="card"><h3>Network topology</h3><div id="graphStats"></div></article></div><details><summary>Vocabulary growth curve and protocol</summary><div id="growth" class="tablewrap"></div></details></section>
<p class="small">Source manifest SHA-256: PAYLOAD.sources_manifest_sha256. Raw vectors, source IDs, prompt/response snapshots and exact measures remain in local artifacts and the linked ResearchGraph. Date/sense-sensitive semantic change is not inferred from author identity.</p></main>
<script>const D=PAYLOAD;const F=['me','plato','parmenides','aristotle'],L={me:'Your essay',plato:'Plato',parmenides:'Parmenides',aristotle:'Aristotle'},C={me:'#edaa59',plato:'#67d4e8',parmenides:'#b69aff',aristotle:'#8fd28f'};const family=document.querySelector('#family');const fmt=(x,n=3)=>x==null?'—':Number(x).toFixed(n);function label(f){return L[f]||f}function showProfiles(){let fs=family.value==='all'?F:[family.value];document.querySelector('#profiles').innerHTML=fs.map(f=>{let x=D.families[f];return `<article class="card"><div>${x.label}</div><div class="metric">${x.tokens.toLocaleString()} tokens</div><div class="small">${x.documents.toLocaleString()} source units · ${x.types.toLocaleString()} types · H=${fmt(x.entropy_bits,2)} bits</div><div class="small">TTR ${fmt(x.mean_ttr,3)} · RTTR ${fmt(x.mean_rttr,2)} · CTTR ${fmt(x.mean_cttr,2)} · zlib ${fmt(x.mean_zlib_ratio,2)}</div><div class="small">Count-model H ${fmt(x.heldout_count_model_cross_entropy,2)} bits · perplexity ${fmt(x.mean_heldout_perplexity,1)} · n=${x.heldout_count_model_units}</div></article>`}).join('')}
function showProbes(){document.querySelector('#probes').innerHTML=D.probes.map(x=>`<tr><td><b>${x.term}</b></td><td>${x.count}</td>${F.map(f=>`<td>${x.families[f]}</td>`).join('')}</tr>`).join('')}
function showAssociations(){document.querySelector('#associations').innerHTML=D.associations.map(x=>`<tr><td>${x.terms.join(' ↔ ')}</td><td>${x.count}</td><td>${fmt(x.pmi,2)}</td><td>${fmt(x.ppmi,2)}</td><td>${fmt(x.npmi,3)}</td><td>${fmt(x.lift,2)}</td><td>${fmt(x.confidence,4)}</td><td>${fmt(x.conviction,3)}</td><td>${fmt(x.logdice,2)}</td><td>${fmt(x.llr,1)}</td><td>${F.map(f=>label(f)+': '+x.families[f]).join(' · ')}</td></tr>`).join('')}
function draw(id,nodes,edges,detail,kind){
 const svg=document.querySelector('#'+id),ns='http://www.w3.org/2000/svg';svg.replaceChildren();
 let N=nodes,E=edges,f=family.value;
 if(kind==='gram'&&f!=='all')N=N.filter(n=>n.families[f]>0);
 if(kind==='word'&&f!=='all')E=E.filter(e=>e.families[f]>0);
 if(kind==='word'&&f!=='all'){let incident=new Set(E.flatMap(e=>[e.source,e.target]));N=N.filter(n=>incident.has(n.id))}
 let ids=new Set(N.map(n=>n.id));E=E.filter(e=>ids.has(e.source)&&ids.has(e.target));
 if(kind==='gram'&&f!=='all')E=E.filter(e=>e.families[f]>0);
 let pos={},max=N.reduce((m,x)=>Math.max(m,x.count||x.weighted_degree||1),1);
 N.forEach((x,i)=>{let a=i*2.399963,r=30+30*Math.sqrt(i);pos[x.id]=[600+r*Math.cos(a),285+r*.78*Math.sin(a)]});
 function el(t,a){let x=document.createElementNS(ns,t);for(const [k,v] of Object.entries(a))x.setAttribute(k,v);svg.append(x);return x}
 if(kind==='gram'){let defs=el('defs',{}),mk=document.createElementNS(ns,'marker');mk.setAttribute('id','arr-'+id);mk.setAttribute('markerWidth','8');mk.setAttribute('markerHeight','8');mk.setAttribute('refX','6');mk.setAttribute('refY','3');mk.setAttribute('orient','auto');let p=document.createElementNS(ns,'path');p.setAttribute('d','M0,0 L0,6 L7,3 z');p.setAttribute('fill','#91a4bc');mk.append(p);defs.append(mk)}
 E.forEach(e=>{let a=pos[e.source],b=pos[e.target];if(!a||!b)return;let w=kind==='concept'?1+Math.max(0,(e.cosine-.4)*5):1+Math.log2(e.count||1);el('line',{x1:a[0],y1:a[1],x2:b[0],y2:b[1],'stroke-width':Math.min(4,w),...(kind==='gram'?{'marker-end':'url(#arr-'+id+')'}:{})})});
 N.forEach(x=>{let p=pos[x.id],v=x.count||x.weighted_degree||1,c=el('circle',{cx:p[0],cy:p[1],r:5+10*Math.sqrt(v/max),fill:kind==='concept'?'#b69aff':C[x.family]||'#67d4e8'});
 c.onclick=()=>{let es=E.filter(e=>e.source===x.id||e.target===x.id).sort((a,b)=>(b.count||b.cosine)-(a.count||a.cosine)).slice(0,10),msg;
 if(kind==='word')msg=`${x.id}: degree ${x.degree}, weighted degree ${x.weighted_degree}, PageRank ${fmt(x.pagerank,5)}. Links: `+es.map(e=>`${e.source}—${e.target} (n=${e.count})`).join('; ');
 else if(kind==='gram')msg=`${x.id} · total ${x.count}; family counts `+F.map(f=>label(f)+': '+x.families[f]).join(' · ')+'. Continuations: '+es.map(e=>`${e.source} → ${e.target} (n=${e.count}; ${F.map(f=>label(f)+': '+e.families[f]).join(', ')})`).join(' | ');
 else msg=`${x.id} · cosine links: `+es.map(e=>`${e.source} ↔ ${e.target}: ${fmt(e.cosine)}`).join(' · ');
 document.querySelector('#'+detail).textContent=msg;let t=el('text',{x:p[0]+7,y:p[1]+4});t.textContent=x.id};});return {N,E}
}
function drawWords(){let z=draw('wordGraph',D.network.nodes,D.network.edges,'wordDetail','word');document.querySelector('#networkMeta').textContent=`${z.N.length} displayed words · ${z.E.length} co-occurrence links · full network ${D.network.all_nodes} nodes / ${D.network.all_edges} edges. Click for weighted degree and PageRank.`}
function drawGrams(){let g=D.gram_networks[document.querySelector('#gramSize').value],z=draw('gramGraph',g.nodes,g.edges,'gramDetail','gram');document.querySelector('#gramMeta').textContent=`${z.N.length} visible grams · ${z.E.length} directed overlapping-gram links. Node radius=count; line width=continuation count. Layout is only a spiral.`}
function drawLatent(){let svg=document.querySelector('#latentGraph'),ns='http://www.w3.org/2000/svg';svg.replaceChildren();let fs=family.value==='all'?F:[family.value],P=D.latent_points.filter(p=>fs.includes(p.family));let xs=P.map(p=>p.pca2[0]),ys=P.map(p=>p.pca2[1]),xmin=Math.min(...xs),xmax=Math.max(...xs),ymin=Math.min(...ys),ymax=Math.max(...ys);function sx(x){return 40+1120*(x-xmin)/(xmax-xmin||1)}function sy(y){return 535-500*(y-ymin)/(ymax-ymin||1)}P.forEach(p=>{let c=document.createElementNS(ns,'circle');c.setAttribute('cx',sx(p.pca2[0]));c.setAttribute('cy',sy(p.pca2[1]));c.setAttribute('r',p.family==='me'?4:2.3);c.setAttribute('fill',C[p.family]);c.setAttribute('opacity','.72');c.onclick=()=>{let detail={source_id:p.source_id,family:label(p.family),cluster:p.cluster,text:p.text,nearest_neighbors:p.neighbors,concept_keyword_cosines:p.keywords,student_logits:p.student_logits,student_steps:p.student_model_steps};document.querySelector('#latentDetail').textContent=JSON.stringify(detail,null,2)};svg.append(c)});document.querySelector('#latentMeta').textContent=`${P.length} source units shown · MiniLM ${D.transformer.shape[1]}D → PCA2 view; ${D.transformer.cluster_count} k-means clusters in PCA32. Cluster and coordinates are exploratory.`;document.querySelector('#legend').innerHTML=fs.map(f=>`<span><i class="dot" style="background:${C[f]}"></i>${label(f)} · ${D.families[f].documents}</span>`).join('');document.querySelector('#centroidTable').innerHTML='<table><thead><tr><th>Family</th>'+F.map(f=>`<th>${label(f)}</th>`).join('')+'</tr></thead><tbody>'+F.map(f=>`<tr><td>${label(f)}</td>${F.map(g=>`<td>${fmt(D.transformer.family_centroid_cosine[f][g],4)}</td>`).join('')}</tr>`).join('')+'</tbody></table>'}
function drawConcept(){let z=draw('conceptGraph',D.concept_network.nodes,D.concept_network.edges,'conceptDetail','concept');let f=family.value;document.querySelector('#conceptMeta').textContent=`${z.N.length} keyword nodes · ${z.E.length} cosine links. `+(f==='all'?'':`Top linked source units for ${label(f)} are in the detail panel after selecting a concept.`)}
function showModels(){document.querySelector('#modelMeta').innerHTML=Object.entries(D.transformer.student_models).map(([k,v])=>`<article class="card"><b>Tiny student · ${k}</b><div class="metric">${v.parameters.toLocaleString()} params</div><div class="small">checkpoint step ${v.step} · watermark ${v.watermark} · unique training records ${v.training_data_unique_records} · SHA ${v.checkpoint_sha256.slice(0,16)}…</div></article>`).join('')+`<article class="card"><b>Cached teacher outputs</b><div class="metric">${D.local_models.length} local Laya cases</div><div class="small">Qwen raw completion attached where requested; no token logprobs in this run.</div></article>`;let fs=D.local_models.filter(r=>family.value==='all'||(family.value==='me'?r.source_case_id.startsWith('e'):family.value==='aristotle'?r.source_case_id.startsWith('a'):false));let fs2=fs.map(r=>`<details><summary>${r.provider} · ${r.source_case_id} · ${r.mode} · ${r.metric_snapshot.correct}/${r.metric_snapshot.heads} diagnostic matches</summary><pre class="small">SOURCE: ${r.source_text}\nLaya score distributions / raw Qwen completion:\n${JSON.stringify({answers:r.answers,qwen:r.raw_qwen&&r.raw_qwen.choices?.[0]?.message?.content,qwen_probability_status:r.qwen_probability_status},null,2)}</pre></details>`).join('');document.querySelector('#teacherRows').innerHTML=fs2||'<p>No previous local teacher cases match this family filter; source-wide tiny-student logits are in the latent point detail.</p>'}
function showCoverage(){document.querySelector('#coverage').innerHTML='<table><thead><tr><th>Measure family</th><th>Evidence/status</th></tr></thead><tbody>'+D.coverage.map(x=>`<tr><td>${x.measure}</td><td class="text">${x.status}</td></tr>`).join('')+'</tbody></table>'}
function showComparisons(){document.querySelector('#compareRows').innerHTML='<table><thead><tr><th>P</th><th>Q</th><th>KL P→Q</th><th>KL Q→P</th><th>JS</th></tr></thead><tbody>'+D.comparisons.map(x=>`<tr><td>${label(x.p)}</td><td>${label(x.q)}</td><td>${fmt(x.kl_p_q_bits,3)}</td><td>${fmt(x.kl_q_p_bits,3)}</td><td>${fmt(x.js_bits,3)}</td></tr>`).join('')+'</tbody></table>';let g=D.graph_metrics;document.querySelector('#graphStats').innerHTML=`<div class="metric">${g.nodes.toLocaleString()} nodes · ${g.edges.toLocaleString()} edges</div><p>${g.components} components · density ${fmt(g.density,5)} · clustering ${fmt(g.average_clustering,4)}</p><p>Sampled largest-component unweighted path mean: ${fmt(g.sampled_largest_component_path_mean,3)} (${g.path_sample_origins.length} fixed-seed origins)</p><p>Small-world: ${g.small_world_status} · Power law: ${g.power_law_status}</p>`;document.querySelector('#growth').innerHTML='<p>'+D.count_model.model+' · alpha='+D.count_model.alpha+' · split='+D.count_model.split+'</p><table><thead><tr><th>Processed tokens</th><th>Vocabulary types</th></tr></thead><tbody>'+D.vocabulary_growth.map(x=>`<tr><td>${x.tokens}</td><td>${x.types}</td></tr>`).join('')+'</tbody></table>'}
function render(){document.querySelector('#sourcePin').textContent='Source manifest SHA-256 '+D.sources_manifest_sha256;showProfiles();showProbes();showAssociations();drawWords();drawGrams();drawLatent();drawConcept();showModels();showCoverage();showComparisons()}family.addEventListener('change',render);document.querySelector('#gramSize').addEventListener('change',drawGrams);render();</script>'''
page=page.replace('PAYLOAD.sources_manifest_sha256',payload['sources_manifest_sha256']).replace('PAYLOAD',json.dumps(payload,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c'))
student_path=ROOT/'unified-student.json'
if student_path.exists():
 student=json.loads(student_path.read_text());run=Path(student['run'])
 if (run/'research-graph-receipt.json').exists():student['research_graph']=json.loads((run/'research-graph-receipt.json').read_text())
 panel=Path(__file__).with_name('unified_student_panel.html').read_text()
 values={'UNIFIED_REPORT':student,'UNIFIED_INPUT':json.loads((run/'real-input.json').read_text()),
  'UNIFIED_PROBES':json.loads((run/'real-probes.json').read_text()),
  'UNIFIED_OBSERVER_REQUESTS':json.loads((run/'observer-prompts.json').read_text()) if (run/'observer-prompts.json').exists() else {},
  'UNIFIED_SPEC_TRIAL':json.loads((ROOT/'unified-spec-trial.json').read_text()) if (ROOT/'unified-spec-trial.json').exists() else None,
  'UNIFIED_OBJECTS':json.loads((Path(student['source_run'])/'candidate.json').read_text())['objects']}
 for token,value in values.items():panel=panel.replace(token,json.dumps(value,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c'))
 projector="""function(o){let t=['OBS_SEQ'];let b=v=>v==null?'MISSING':String(Math.min(10,Math.floor(v*10+.5)));for(let n of ['jev','laya','qwen','qwen-feedback']){t.push('OBS:'+n);for(let[h,cs]of [['network_fit',['per_choice','common_good','neither','unresolved']],['support',['supported','unsupported','unresolved']]]){let a=o[n]?.answers?.[h]||{};t.push('HEAD:'+h,'CHOICE:'+(a.choice||'MISSING'),'CONF:'+b(a.confidence));for(let c of cs)t.push('P:'+c+':'+b(a.probabilities?.[c]));t.push('END_HEAD')}t.push('END_OBS')}return t.concat('END_OBS_SEQ')}"""
 panel=panel.replace('UNIFIED_TOKEN_FUNCTION', '('+projector+')')
 fresh_path=ROOT/'fresh-s3-tower.json'
 if fresh_path.exists():
  fresh=json.loads(fresh_path.read_text());fresh_run=Path(fresh['run']);prompts={};fresh['full_source']=(fresh_run/'source.txt').read_text()
  if (fresh_run/'checkpoint-replay.json').exists():fresh['checkpoint_replay']=json.loads((fresh_run/'checkpoint-replay.json').read_text())
  if (fresh_run/'research-graph-receipt.json').exists():fresh['research_graph']=json.loads((fresh_run/'research-graph-receipt.json').read_text())
  for row in fresh['records']:
   prompts[row['id']]={str(p.relative_to(fresh_run/row['id'])):json.loads(p.read_text()) for p in (fresh_run/row['id']).glob('*/*/*.json')}
  fresh_panel=Path(__file__).with_name('fresh_s3_panel.html').read_text()
  for token,value in {'FRESH_S3_REPORT':fresh,'FRESH_S3_PROMPTS':prompts}.items():fresh_panel=fresh_panel.replace(token,json.dumps(value,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c'))
  panel=panel.replace('unifiedStudent','historicalUnifiedStudent')
  panel='<div id="unifiedStudent"></div>'+fresh_panel+'<h2>Historical experiments below</h2>'+panel
 connection_path=ROOT/'connectivity-student.json'
 if connection_path.exists():
  connections=json.loads(connection_path.read_text());connection_run=Path(connections['run'])
  if (connection_run/'research-graph-receipt.json').exists():connections['research_graph']=json.loads((connection_run/'research-graph-receipt.json').read_text())
  requests={str(p.relative_to(connection_run)):json.loads(p.read_text()) for p in connection_run.glob('connectivity-architecture/*/*/*.json')}
  connection_panel=Path(__file__).with_name('connectivity_panel.html').read_text()
  for token,value in {'CONNECTIVITY_REPORT':connections,'CONNECTIVITY_PROMPTS':requests}.items():connection_panel=connection_panel.replace(token,json.dumps(value,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c'))
  panel=panel.replace('<div id="unifiedStudent"></div>','<div id="previousStudent"></div>')
  panel='<div id="unifiedStudent"></div>'+connection_panel+panel
 bridge_path=ROOT/'philosophy-spec-bridge.json'
 if not bridge_path.exists():bridge_path=ROOT/'philosophy-spec-bridge-progress.json'
 if bridge_path.exists():
  bridge=json.loads(bridge_path.read_text());bridge_run=Path(bridge['run'])
  if (bridge_run/'student-metrics.json').exists():bridge['student_metrics']=json.loads((bridge_run/'student-metrics.json').read_text())
  if (bridge_run/'all-student-logits.json').exists():bridge['all_student_logits']=json.loads((bridge_run/'all-student-logits.json').read_text())
  if (bridge_run/'research-graph-receipt.json').exists():bridge['research_graph']=json.loads((bridge_run/'research-graph-receipt.json').read_text())
  grams=json.loads((bridge_run/'lexical/connected-grams.json').read_text());keyword=json.loads((bridge_run/'lexical/keyword-network.json').read_text());graphs={**grams,'keyword':keyword,'typed':bridge['source_graph'],'concept':bridge['neural']['concept_network']}
  for n,g in grams.items():
   records=[json.loads(x) for x in (bridge_run/'lexical'/('terms.jsonl' if n=='1' else 'ngrams-'+n+'.jsonl')).read_text().splitlines() if x]
   g['nodes']=[{'id':v['term'] if n=='1' else ' '.join(v['tokens']),'count':v['count']} for v in records]
   ids={v['id'] for v in g['nodes']};assert all(e['source'] in ids and e['target'] in ids for e in g['edges'])
   g['description']='All counted grams retained; display shows the most frequent 70. Lexical tokenizer excludes digits; exact spec identifiers remain in the typed network.'
  graphs['typed']={**bridge['source_graph'],'edges':[{**e,'source':bridge['source_graph']['nodes'][e['source']]['id'],'target':bridge['source_graph']['nodes'][e['target']]['id']} for e in bridge['source_graph']['edges']]}
  logical_nodes=[];logical_edges=[]
  for stage in bridge['stages']:
   for unit,candidate in stage['feedback']['symbolic']['by_unit'].items():
    prefix='L'+str(stage['layer'])+':'+unit+':';known={}
    for atom in candidate['atoms']:
     ident=prefix+'atom:'+atom['symbol'];known[atom['symbol']]=ident;logical_nodes.append({'id':ident,'label':atom['symbol'],'kind':atom['kind'],'source_unit':unit,'source_quote':atom['source_quote'],'authority':'Qwen candidate, not admitted'})
    for flow in candidate['flows']:
     ident=prefix+'flow:'+flow['id'];known[flow['id']]=ident;logical_nodes.append({'id':ident,'label':flow['rule'],'kind':'inference','source_unit':unit,'flow':flow,'checks':stage['final_checks'].get(unit)})
     for i,formula in enumerate(flow['premises']):
      pid=prefix+flow['id']+':premise:'+str(i);logical_nodes.append({'id':pid,'label':formula,'kind':'formula','source_unit':unit});logical_edges.append({'source':pid,'target':ident,'role':'premise','position':i,'source_unit':unit})
    for i,composition in enumerate(candidate['compositions']):
     ident=prefix+'composition:'+str(i);logical_nodes.append({'id':ident,'label':composition['kind'],'kind':'composition','source_unit':unit,'members':composition['members']})
     for j,member in enumerate(composition['members']):
      if member in known:logical_edges.append({'source':known[member],'target':ident,'role':'member','position':j,'source_unit':unit})
  graphs['logic']={'nodes':logical_nodes,'edges':logical_edges,'description':'Higher-order teacher candidates with local symbol scope and source-unit provenance. Unsupported proposals remain visible.'}
  graphs['cross']={'nodes':[{'id':u['source_id']} for u in bridge['neural']['units']]+list({n['source_id']:{'id':n['source_id']} for u in bridge['neural']['units'] for n in u['nearest_philosophy']}.values()),'edges':[{'source':u['source_id'],'target':n['source_id'],'cosine':n['cosine']} for u in bridge['neural']['units'] for n in u['nearest_philosophy']],'description':'Fresh spec vectors compared to retained philosophy vectors; similarity does not establish identity.'}
  prompts={str(p.relative_to(bridge_run)):json.loads(p.read_text()) for p in bridge_run.rglob('*.json') if p.name in ['request.json','response.json'] and 'failed' not in str(p.relative_to(bridge_run))}
  bridge_tools={}
  for p in (bridge_run/'lexical').iterdir():
   if p.suffix=='.json':bridge_tools[p.name]=json.loads(p.read_text())
   elif p.suffix=='.jsonl':bridge_tools[p.name]=[json.loads(x) for x in p.read_text().splitlines() if x]
   elif p.suffix=='.csv':bridge_tools[p.name]=p.read_text()
  bridge_panel=Path(__file__).with_name('philosophy_spec_panel.html').read_text()
  for token,value in {'BRIDGE_REPORT':bridge,'BRIDGE_GRAPHS':graphs,'BRIDGE_PROMPTS':prompts,'BRIDGE_TOOLS':bridge_tools}.items():bridge_panel=bridge_panel.replace(token,json.dumps(value,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c'))
  panel=panel.replace('<div id="unifiedStudent"></div>','<div id="previousBridgeStudent"></div>');panel='<div id="unifiedStudent"></div>'+bridge_panel+panel
 page=page.replace('<main>', '<main>'+panel)
(ROOT/'network.html').write_text(page)
print(json.dumps({'path':str(ROOT/'network.html'),'bytes':len(page),'corpus_units':len(sources),'associations':len(assocout),'grams':{k:[len(v['nodes']),len(v['edges'])] for k,v in gramnet.items()},'transformer_points':len(payload['latent_points']),'local_model_observations':len(local),'coverage_items':len(coverage)}))
