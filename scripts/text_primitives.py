"""Source-pinned, model-free lexical observations for the SHG experiment."""
import argparse,collections,ctypes,ctypes.util,hashlib,json,math,re
from pathlib import Path
from lexical_metrics import association, profiles, keyword_graph
TOKEN=re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)?",re.UNICODE)
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def stemmer():
 lib=ctypes.CDLL(ctypes.util.find_library('stemmer'));lib.sb_stemmer_new.argtypes=[ctypes.c_char_p,ctypes.c_char_p];lib.sb_stemmer_new.restype=ctypes.c_void_p
 lib.sb_stemmer_stem.argtypes=[ctypes.c_void_p,ctypes.c_char_p,ctypes.c_int];lib.sb_stemmer_stem.restype=ctypes.c_void_p;lib.sb_stemmer_length.argtypes=[ctypes.c_void_p];lib.sb_stemmer_length.restype=ctypes.c_int;lib.sb_stemmer_delete.argtypes=[ctypes.c_void_p]
 handle=lib.sb_stemmer_new(b'english',b'UTF_8');assert handle
 def apply(word):
  b=word.encode();p=lib.sb_stemmer_stem(handle,b,len(b));return ctypes.string_at(p,lib.sb_stemmer_length(handle)).decode()
 return apply,lambda:lib.sb_stemmer_delete(handle)
def analyze(documents,out,window=5,min_count=3):
 assert window>0 and min_count>0;out=Path(out);out.mkdir(parents=True,exist_ok=True);tf=[];df=collections.Counter();freq=collections.Counter();grams={n:collections.Counter() for n in (2,3)};pairs=collections.Counter();pair_sources=collections.defaultdict(collections.Counter);marginals=collections.Counter();total=0;tokens_total=0
 for doc in documents:
  tokens=[m.group().casefold() for m in TOKEN.finditer(doc['text'])];counts=collections.Counter(tokens);tf.append(counts);df.update(counts.keys());freq.update(counts);tokens_total+=len(tokens)
  for n,c in grams.items():c.update(tuple(tokens[i:i+n]) for i in range(len(tokens)-n+1))
  for i,a in enumerate(tokens):
   for b in tokens[i+1:i+1+window]:
    pair_sources[tuple(sorted((a,b)))][doc['id']]+=1;pairs[(a,b)]+=1;pairs[(b,a)]+=1;marginals[a]+=1;marginals[b]+=1;total+=2
 def write(name,rows):
  p=out/name
  with p.open('w') as f:
   for row in rows:f.write(json.dumps(row,ensure_ascii=False)+'\n')
  return {'path':str(p.resolve()),'sha256':digest(p)}
 files={};files['occurrences']=write('token-occurrences.jsonl',({'source_id':d['id'],'position':i,'start':m.start(),'end':m.end(),'term':m.group().casefold()} for d in documents for i,m in enumerate(TOKEN.finditer(d['text']))));files['sources']=write('sources.jsonl',documents);files['terms']=write('terms.jsonl',({'term':t,'count':c,'document_frequency':df[t]} for t,c in freq.most_common()))
 stem,close=stemmer()
 try:files['normalization']=write('normalization.jsonl',({'term':t,'stem':stem(t),'algorithm':'Snowball english','lemma':None} for t in sorted(freq)))
 finally:close()
 for n,c in grams.items():files['ngrams'+str(n)]=write('ngrams-'+str(n)+'.jsonl',({'tokens':t,'count':v} for t,v in c.most_common()))
 files['association']=write('association.jsonl',({'terms':[a,b],'count':c,**association(c,marginals[a],marginals[b],total)} for (a,b),c in pairs.items() if c>=min_count))
 document_profiles,term_profiles=profiles(documents,TOKEN)
 files['document_metrics']=write('document-metrics.jsonl',document_profiles)
 files['dispersion']=write('dispersion.jsonl',term_profiles)
 graph=keyword_graph(pairs,min_count)
 for edge in graph['edges']:edge['source_units']=dict(pair_sources[(edge['source'],edge['target'])])
 gp=out/'keyword-network.json';gp.write_text(json.dumps(graph));files['keyword_network']={'path':str(gp.resolve()),'sha256':digest(gp)}

 N=len(documents);files['tfidf']=write('tfidf.jsonl',({'source_id':d['id'],'weights':{t:(1+math.log(c))*(1+math.log((1+N)/(1+df[t]))) for t,c in counts.items()}} for d,counts in zip(documents,tf)))
 ranks=freq.most_common();files['zipf']=write('zipf.jsonl',({'term':t,'rank':i,'count':c,'rank_times_count':i*c} for i,(t,c) in enumerate(ranks,1)))
 manifest={'schema':'text-primitives-v1','documents':N,'tokens':tokens_total,'vocabulary':len(freq),'families':dict(collections.Counter(d['family'] for d in documents)),'window':window,'pair_events':total,'min_pair_count':min_count,'normalization':'casefold; Snowball stems retained separately; logical function words kept','lemmatization':'not implemented; lemma null, no invented equivalence','tfidf':'(1+ln(tf)) * (1+ln((1+N)/(1+df)))','pmi':'log2(count(a,b)*pair_events/(context_marginal(a)*context_marginal(b)))','zipf':'empirical rank/frequency observations; no assumed exact law','authority':'Counts and lexical associations only; no semantic identity or logical entailment','files':files}
 stages={'source':['sources'],'tokenize':['terms','occurrences'],'stem':['normalization'],'ngrams':['ngrams2','ngrams3'],'cooccurrence':['association','keyword_network'],'ppmi':['association'],'tfidf':['tfidf','dispersion','document_metrics'],'zipf':['zipf']}
 (out/'artifact-pins.sexp').write_text('('+'\n'.join('(:'+stage+' '+ ' '.join('(:path '+json.dumps(files[k]['path'])+' :sha256 '+json.dumps(files[k]['sha256'])+')' for k in keys)+')' for stage,keys in stages.items())+')\n')
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2));return manifest

def sources():
 docs=[];seen=set()
 def add(family,id,text,pin):
  key=(family,id)
  if key not in seen:seen.add(key);docs.append({'id':id,'family':family,'text':text,'source_ref':pin})
 essay=Path('/home/user0/truth.txt');text=essay.read_text();sha=digest(essay)
 for i,m in enumerate(re.finditer(r'\S[\s\S]*?(?=\n\s*\n|\Z)',text),1):
  t=m.group().rstrip();add('me','essay:paragraph:'+str(i),t,{'path':str(essay),'sha256':sha,'start':m.start(),'end':m.start()+len(t)})
 root=Path('/home/user0/.local/state/turn-transport/aristotle-two-towers-v1/sources')
 for family,path in [('plato',root/'plato-parmenides/paragraphs.jsonl'),('parmenides',root/'parmenides/fragments.jsonl')]:
  for line in path.open():
   r=json.loads(line);add(family,r['id'],r['text'],r['source_ref'])
 p=Path('/home/user0/research-aristotle-semantic-observation/corpusGraph/data/aristotle-disrpt-classifier-transfer-v1/aristotle-disrpt-classifier-predictions-v1.jsonl');sha=digest(p)
 for lineno,line in enumerate(p.open(),1):
  r=json.loads(line)
  if r['classifier']!='stacked':continue
  for side in ('arg1','arg2'):add('aristotle',r[side+'_ref'],r[side+'_text'],{'path':str(p),'sha256':sha,'jsonl_line':lineno,'field':side+'_text','unit_ref':r[side+'_ref']})
 return docs
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--out',default='working/text-primitives');args=ap.parse_args();print(json.dumps(analyze(sources(),args.out),indent=2))
