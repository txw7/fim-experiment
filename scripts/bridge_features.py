"""Execute existing philosophy feature tools on a separately pinned source lane."""
import collections,hashlib,importlib.util,json,math,os,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PHIL=ROOT/'working/text-primitives'
def save(path,value):Path(path).write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False,default=float)+'\n')
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def lexical(run):
 import text_primitives as primitive,extended_text_metrics as extended
 import spacy,morfessor
 from rakun2 import RakunKeyphraseDetector
 from rapidfuzz.distance import DamerauLevenshtein
 from sacrebleu.metrics import BLEU
 from scipy.stats import hypergeom
 import networkx as nx
 units=json.loads((run/'source-units.json').read_text());out=run/'lexical';out.mkdir();manifest=primitive.analyze(units,out,min_count=1);extended.ROOT=out;extended.main()
 tokens={r['id']:[m.group().casefold() for m in primitive.TOKEN.finditer(r['text'])] for r in units};grams={}
 for n in [1,2,3]:
  counts=collections.Counter();edges=collections.Counter();refs=collections.defaultdict(set)
  for ident,ts in tokens.items():
   gs=[' '.join(ts[i:i+n]) for i in range(len(ts)-n+1)];counts.update(gs)
   for a,b in zip(gs,gs[1:]):edges[a,b]+=1;refs[a,b].add(ident)
  grams[str(n)]={'nodes':[{'id':t,'count':v} for t,v in counts.most_common(120)],'edges':[{'source':a,'target':b,'count':v,'source_units':sorted(refs[a,b])} for (a,b),v in edges.items()]}
 save(out/'connected-grams.json',grams)
 nlp=spacy.load('en_core_web_sm');detector=RakunKeyphraseDetector(dict(num_keywords=10,merge_threshold=1.1,alpha=.3,token_prune_len=3));rows=[]
 for r in units:
  parsed=nlp(r['text']);dist=[abs(t.i-t.head.i) for t in parsed if not t.is_punct and t.head!=t]
  rows.append({'source_id':r['id'],'source_ref':r['source_ref'],'keywords':detector.find_keywords(r['text'],input_type='string'),'dependency_distance_mean':sum(dist)/len(dist) if dist else None,'dependency_edges':[{'token':t.text,'lemma':t.lemma_,'head':t.head.text,'relation':t.dep_,'start':t.idx,'end':t.idx+len(t)} for t in parsed],'spec_identifier_occurrences':[{'identifier':m.group(),'start':m.start(),'end':m.end()} for m in re.finditer(r'\b(?:[A-Z]+\d(?:\.\d)?|[A-Z][A-Z_]+)\b',r['text'])]})
 save(out/'parser-keywords.json',rows)
 # Original MDL tool runs on this lane's vocabulary, without touching the philosophy model.
 model=morfessor.BaselineModel();counts=collections.Counter(t for ts in tokens.values() for t in ts);model.load_data((c,w) for w,c in counts.items());epochs,cost=model.train_batch(max_epochs=5)
 save(out/'morphology.json',{'epochs':epochs,'cost':cost,'terms':[{'term':w,'segments':model.viterbi_segment(w)[0],'score':model.viterbi_segment(w)[1]} for w in counts]})
 # Run the same enabled TAACO options, this time for every source unit.
 taaco=ROOT/'deps/text-tools/TAACO';inputs=out/'taaco-input';inputs.mkdir()
 for r in units:(inputs/(r['id']+'.txt')).write_text(r['text'])
 smoke=(ROOT/'scripts/text_tool_smoke.py').read_text();scope={};exec(smoke[smoke.index('    keys='):smoke.index('    sys.path.insert')].replace('    ',''),scope)
 sys.path.insert(0,str(taaco));old=Path.cwd()
 try:os.chdir(taaco);__import__('TAACOnoGUI').runTAACO(str(inputs.resolve())+'/',str((out/'taaco.csv').resolve()),scope['opts'])
 finally:os.chdir(old)
 philosophy_counts=collections.Counter({r['term']:r['count'] for r in map(json.loads,(PHIL/'terms.jsonl').read_text().splitlines())});spec_counts=counts
 comparisons={'spec_vs_philosophy':extended.compare(spec_counts,philosophy_counts),'source_unit_comparisons':[{'source_id':r['id'],**extended.compare(collections.Counter(tokens[r['id']]),philosophy_counts)} for r in units]}
 save(out/'domain-comparisons.json',comparisons)
 graph=json.loads((out/'keyword-network.json').read_text());G=nx.Graph();G.add_weighted_edges_from((e['source'],e['target'],e['count']) for e in graph['edges']);source_graph=json.loads((run/'source-graph.json').read_text());H=nx.DiGraph();H.add_nodes_from(n['id'] for n in source_graph['nodes']);H.add_edges_from((source_graph['nodes'][e['source']]['id'],source_graph['nodes'][e['target']]['id']) for e in source_graph['edges'])
 descriptive={'lexical':{'nodes':len(G),'edges':G.number_of_edges(),'components':nx.number_connected_components(G),'pagerank':nx.pagerank(G,weight='weight'),'egonets':{n:{'degree':G.degree(n),'density':nx.density(nx.ego_graph(G,n))} for n in G},'spreading_activation':{}},'typed':{'nodes':len(H),'directed_edges':H.number_of_edges(),'weak_components':nx.number_weakly_connected_components(H),'max_out_degree':max(dict(H.out_degree()).values()),'repeated_lexeme_links':sum(e['role']=='binding' for e in source_graph['edges']),'predicate_nodes_per_100_words':100*sum(n['kind'] not in ['agent','stage','state','event','pipe','use'] for n in source_graph['nodes'])/sum(len(ts) for ts in tokens.values()),'edges_per_predicate_node':H.number_of_edges()/sum(n['kind'] not in ['agent','stage','state','event','pipe','use'] for n in source_graph['nodes'])}}
 for cue in ['identity','source','provider','generation']:
  if cue not in G:continue
  activation={cue:1.};total=collections.Counter(activation)
  for _ in range(3):
   nxt=collections.Counter()
   for a,v in activation.items():
    neighbors=G[a];mass=sum(e['weight'] for e in neighbors.values())
    for b,e in neighbors.items():nxt[b]+=.7*v*e['weight']/mass
   total.update(nxt);activation=nxt
  descriptive['lexical']['spreading_activation'][cue]=dict(total)
 save(out/'topology.json',descriptive)
 optional={}
 try:
  from grakel import Graph,WeisfeilerLehman,VertexHistogram
  def kernelgraph(d):return Graph({(e['source'],e['target']):1 for e in d['edges']},node_labels={n['id']:n['id'] for n in d['nodes']})
  prior=json.loads((PHIL/'keyword-network.json').read_text());kernel=WeisfeilerLehman(n_iter=2,base_graph_kernel=VertexHistogram,normalize=True);optional['graph_kernel']={'status':'executed','matrix':kernel.fit_transform([kernelgraph(graph),kernelgraph(prior)]).tolist(),'definition':'WL lexical-label graph similarity, not semantic identity'}
 except Exception as e:optional['graph_kernel']={'status':'unavailable','reason':type(e).__name__+': '+str(e)}
 save(out/'optional-tools.json',optional)
 save(out/'receipt.json',{'status':'executed','units':len(units),'source_manifest':sha(run/'source-units.json'),'reused_implementations':{str(p):sha(p) for p in [ROOT/'scripts/text_primitives.py',ROOT/'scripts/lexical_metrics.py',ROOT/'scripts/extended_text_metrics.py',ROOT/'scripts/text_tool_smoke.py']},'files':{str(p.relative_to(run)):sha(p) for p in out.rglob('*') if p.is_file()}})
 print('LEXICAL_COMPLETE',flush=True)

def neural(run):
 import numpy as np,torch,joblib
 from transformers import AutoModel,AutoTokenizer
 torch.set_num_threads(2);torch.cuda.is_available=lambda:False
 units=json.loads((run/'source-units.json').read_text());out=run/'neural';out.mkdir(exist_ok=True);stack=Path('/home/user0/research-gold-disrpt/results/disrpt-classifier-stack-v1');sys.path.insert(0,'/home/user0/research-gold-disrpt/corpusGraph')
 from semantic_tower import classifier_stack as cs
 pairs=[{'unit1':a['text'],'unit2':b['text'],'source_id':a['id'],'target_id':b['id']} for a,b in zip(units,units[1:])];features={};pins={};heads={}
 for name,(kind,_) in cs.MODEL_SPECS.items():
  manifest=stack/'backbones'/(name+'.json');original=json.loads(manifest.read_text());path=Path(original['path']);pins[str(manifest)]=sha(manifest)
  try: accessible=path.exists()
  except OSError: accessible=False
  if not accessible:
   repos={'minilm':'sentence-transformers--all-MiniLM-L6-v2','bge':'BAAI--bge-small-en-v1.5','e5':'intfloat--e5-small-v2','nli_minilm':'cross-encoder--nli-MiniLM2-L6-H768','nli_deberta':'cross-encoder--nli-deberta-v3-small','ms_marco':'cross-encoder--ms-marco-MiniLM-L-6-v2'}
   candidates=list((Path('/home/user0/.cache/huggingface/hub')/('models--'+repos[name])/'snapshots').glob('*'));matches=[]
   required={k:v for k,v in original['files'].items() if k in ['model.safetensors','pytorch_model.bin'] or k in ['config.json','tokenizer.json','tokenizer_config.json']}
   for candidate in candidates:
    if all((candidate/k).exists() and sha(candidate/k)==digest for k,digest in required.items()):matches.append(candidate)
   assert matches,'No cached backbone with matching trained weights/tokenizer: '+name
   path=matches[0];print('MATCHED_CACHED_BACKBONE '+name+' '+str(path),flush=True)
  for filename in ['model.safetensors','pytorch_model.bin','config.json','tokenizer.json']:
   if (path/filename).exists():pins[str(path/filename)]=sha(path/filename)
  features[name]=cs._embed_features(path,pairs,out/(name+'.npz')) if kind=='embedding' else cs._pair_model_features(path,pairs,out/(name+'.npz'),nli=kind=='nli')
  print('FROZEN_BACKBONE '+name,flush=True)
 features['stacked']=np.concatenate([features[n] for n in cs.MODEL_SPECS],axis=1)
 for name in [*cs.MODEL_SPECS,'tfidf','stacked']:
  path=stack/'classifiers'/(name+'.joblib');bundle=joblib.load(path);pipe=bundle['pipeline'];x=[p['unit1']+' [SEP] '+p['unit2'] for p in pairs] if name=='tfidf' else features[name];probs=pipe.predict_proba(x);logits=pipe.decision_function(x);pins[str(path)]=sha(path)
  heads[name]={'labels':list(pipe.classes_),'scores':probs.tolist(),'raw_logits':logits.tolist(),'source_pairs':[{'source':p['source_id'],'target':p['target_id']} for p in pairs],'domain':'DISRPT discourse diagnostics; spec transfer not validated','calibration':'not established on specs','backbone_outputs':features[name].tolist() if name in cs.MODEL_SPECS else None}
 import transformer_latents as latents
 tokenizer=AutoTokenizer.from_pretrained(str(latents.MODEL),local_files_only=True);encoder=AutoModel.from_pretrained(str(latents.MODEL),local_files_only=True).eval()
 def embed(texts):
  batch=tokenizer(texts,padding=True,truncation=False,return_tensors='pt');assert batch['input_ids'].shape[1]<=512,'No silent MiniLM truncation'
  with torch.no_grad():hidden=encoder(**batch).last_hidden_state;mask=batch['attention_mask'].unsqueeze(-1);pooled=(hidden*mask).sum(1)/mask.sum(1);return torch.nn.functional.normalize(pooled,p=2,dim=1).numpy()
 vectors=embed([r['text'] for r in units]);prior=np.load(PHIL/'transformer-latents.npz');old=prior['vectors'];ids=prior['source_ids'];cos=vectors@old.T
 concepts=sorted(set([n['label'] for n in json.loads((run/'source-graph.json').read_text())['nodes']]+['truth','being','one','good','identity','scope','premise','conclusion','generation','authorization']));concept_vectors=embed(concepts)
 from sklearn.decomposition import PCA
 pca=PCA(n_components=32,random_state=17).fit(old);latent32=pca.transform(vectors);pca2=PCA(n_components=2,random_state=17).fit(old).transform(vectors)
 neighbors=[]
 for i,r in enumerate(units):
  ix=np.argsort(cos[i])[-6:][::-1];neighbors.append({'source_id':r['id'],'nearest_philosophy':[{'source_id':str(ids[j]),'cosine':float(cos[i,j])} for j in ix],'concept_cosines':[{'concept':concepts[j],'cosine':float((vectors@concept_vectors.T)[i,j])} for j in np.argsort((vectors@concept_vectors.T)[i])[-6:][::-1]],'latent32':latent32[i].tolist(),'pca2':pca2[i].tolist(),'vector384':vectors[i].tolist()})
 np.savez_compressed(out/'latents.npz',vectors=vectors,concept_vectors=concept_vectors,concepts=np.array(concepts),latent32=latent32,pca2=pca2)
 save(out/'features.json',{'classifiers':heads,'units':neighbors,'concept_network':{'nodes':[{'id':c} for c in concepts],'edges':[{'source':a,'target':b,'cosine':float(concept_vectors[i]@concept_vectors[j])} for i,a in enumerate(concepts) for j,b in enumerate(concepts) if i<j and float(concept_vectors[i]@concept_vectors[j])>=.35]},'original_operator_students':latents.local_student_logits([r['text'] for r in units]),'pins':{**pins,str(latents.MODEL/'model.safetensors'):sha(latents.MODEL/'model.safetensors'),str(PHIL/'transformer-latents.npz'):sha(PHIL/'transformer-latents.npz')},'student_transfer':'Original weights inferred on new S3 text; no original checkpoint mutated','embeddings':'384D normalized vectors; PCA fitted on philosophy corpus and applied to specs; cosine is not identity','paired_backbone_token_limit':256})
 print('NEURAL_COMPLETE',flush=True)

if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]).resolve())
