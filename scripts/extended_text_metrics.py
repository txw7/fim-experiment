"""Additional count-based observations using acquired scientific libraries."""
import collections, hashlib, itertools, json, math, random
from pathlib import Path
import networkx as nx
import numpy as np
from scipy.stats import hypergeom
from rapidfuzz.distance import DamerauLevenshtein
from sacrebleu.metrics import BLEU
from text_primitives import TOKEN
from lexical_metrics import entropy

ROOT=Path(__file__).resolve().parents[1]/'working/text-primitives'

def distribution_metrics(counts, bigrams):
    total=sum(counts.values()); events=sum(bigrams.values())
    left=collections.Counter();right=collections.Counter()
    for (a,b),c in bigrams.items():left[a]+=c;right[b]+=c
    joint_entropy=entropy(bigrams.values())
    return dict(entropy_bits=entropy(counts.values()),
        concentration=sum((c/total)**2 for c in counts.values()) if total else None,
        adjacent_pair_events=events, next_given_previous_entropy_bits=joint_entropy-entropy(left.values()),
        previous_given_next_entropy_bits=joint_entropy-entropy(right.values()),
        adjacent_mutual_information_bits=entropy(left.values())+entropy(right.values())-joint_entropy)

def compare(p,q,alpha=.5):
    vocabulary=sorted(p.keys()|q.keys());k=len(vocabulary)
    if not k:return dict(kl_p_q_bits=0,kl_q_p_bits=0,js_bits=0)
    a=np.array([p[t]+alpha for t in vocabulary]);b=np.array([q[t]+alpha for t in vocabulary]);a/=a.sum();b/=b.sum();m=(a+b)/2
    return dict(kl_p_q_bits=float(np.sum(a*np.log2(a/b))),kl_q_p_bits=float(np.sum(b*np.log2(b/a))),
        js_bits=float((np.sum(a*np.log2(a/m))+np.sum(b*np.log2(b/m)))/2),smoothing=alpha,vocabulary=k)

def main():
    documents=[json.loads(s) for s in (ROOT/'sources.jsonl').open()]
    terms=[json.loads(s) for s in (ROOT/'terms.jsonl').open()]
    families=collections.defaultdict(collections.Counter); bigrams=collections.Counter();skipgrams=collections.Counter();counts=collections.Counter();growth=[];seen=set();token_count=0
    tokenized=[];reuse=collections.defaultdict(dict)
    for d in documents:
        ts=[m.group().casefold() for m in TOKEN.finditer(d['text'])];tokenized.append(ts);families[d['family']].update(ts);counts.update(ts)
        for i,a in enumerate(ts):
            seen.add(a);token_count+=1
            if token_count%1000==0:growth.append(dict(tokens=token_count,types=len(seen)))
            if i+1<len(ts):bigrams[(a,ts[i+1])]+=1
            for distance in (2,3):
                if i+distance<len(ts):skipgrams[(a,ts[i+distance],distance)]+=1
        for gram in set(tuple(ts[i:i+3]) for i in range(len(ts)-2)):reuse[gram][d['id']]=d['family']
    growth.append(dict(tokens=token_count,types=len(seen)))
    def dump(name,rows):
        path=ROOT/name
        with path.open('w') as f:
            for row in rows:f.write(json.dumps(row,ensure_ascii=False,allow_nan=False)+'\n')
        return dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    outputs={}
    total=sum(counts.values());lengths={f:sum(c.values()) for f,c in families.items()}
    specificity=[]
    for family,c in families.items():
        for t in sorted(counts):
            observed=c[t];expected=counts[t]*lengths[family]/total
            if observed>expected:
                log_tail=float(hypergeom.logsf(observed-1,total,counts[t],lengths[family]))
                specificity.append(dict(term=t,family=family,count=observed,expected=expected,
                    overrepresentation_neg_log10_p=-log_tail/math.log(10),null='random token allocation conditional on margins; unadjusted'))
    train=collections.Counter(); heldout=[]; train_ids=[]
    for d,ts in zip(documents,tokenized):
        if int(hashlib.sha256(d['id'].encode()).hexdigest(),16)%5==0:heldout.append((d,ts))
        else:train.update(ts);train_ids.append(d['id'])
    denominator=sum(train.values())+.5*(len(train)+1);surprisal=[]
    for d,ts in heldout:
        scores=[-math.log2((train[t]+.5)/denominator) for t in ts]
        mean=sum(scores)/len(scores) if scores else None
        surprisal.append(dict(source_id=d['id'],tokens=len(ts),unknown_tokens=sum(t not in train for t in ts),
            cross_entropy_bits=mean,perplexity=2**mean if mean is not None else None,token_surprisal_bits=scores))
    outputs['surprisal']=dump('count-surprisal.jsonl',surprisal)
    outputs['specificity']=dump('lexical-specificity.jsonl',specificity)
    proportions={f:n/total for f,n in lengths.items()}
    outputs['dispersion']=dump('dispersion-dp.jsonl',(dict(term=t,dp=.5*sum(abs(families[f][t]/count-proportions[f]) for f in families)) for t,count in counts.items()))
    outputs['skipgrams']=dump('skipgrams.jsonl',(dict(tokens=[a,b],distance=distance,gap=distance-1,count=c) for (a,b,distance),c in skipgrams.most_common() if c>=3))
    outputs['reuse']=dump('cross-family-trigrams.jsonl',(dict(tokens=g,source_units=refs) for g,refs in reuse.items() if len(set(refs.values()))>1))
    vocabulary=sorted(counts);buckets=collections.defaultdict(list);variants=[]
    for word in vocabulary:
        for length in range(len(word)-1,len(word)+2):
            for other in buckets[(word[:2],length)]:
                distance=DamerauLevenshtein.distance(word,other,score_cutoff=1)
                if distance<=1:variants.append(dict(terms=[other,word],distance=distance,authority='surface variant candidate, not identity'))
        buckets[(word[:2],len(word))].append(word)
    outputs['variants']=dump('edit-variants.jsonl',variants)
    graph_data=json.loads((ROOT/'keyword-network.json').read_text());g=nx.Graph()
    g.add_nodes_from(n['id'] for n in graph_data['nodes']);g.add_weighted_edges_from((e['source'],e['target'],e['count']) for e in graph_data['edges'])
    components=sorted(nx.connected_components(g),key=len,reverse=True);largest=g.subgraph(components[0]) if components else g
    origins=random.Random(0).sample(sorted(largest),min(64,len(largest)));distance_sum=0;distance_n=0
    for origin in origins:
        ds=nx.single_source_shortest_path_length(largest,origin);distance_sum+=sum(ds.values());distance_n+=len(ds)-1
    graph=dict(nodes=g.number_of_nodes(),edges=g.number_of_edges(),components=len(components),component_sizes=[len(c) for c in components],
        density=nx.density(g),average_clustering=nx.average_clustering(g) if g else 0,
        degree_histogram=nx.degree_histogram(g),sampled_largest_component_path_mean=distance_sum/distance_n if distance_n else None,
        path_sample_origins=origins,path_weights='unweighted hops',small_world_status='not tested',power_law_status='not fitted')
    # ponytail: Self-BLEU is quadratic; deterministic 32-unit sample per family.
    bleu=BLEU(tokenize='none',effective_order=True);self_bleu={}
    for family in families:
        indices=[i for i,d in enumerate(documents) if d['family']==family and tokenized[i]]
        sampled=random.Random(0).sample(indices,min(32,len(indices)));texts=[' '.join(tokenized[i]) for i in sampled]
        self_bleu[family]=dict(mean=sum(bleu.sentence_score(t,texts[:i]+texts[i+1:]).score for i,t in enumerate(texts))/len(texts) if len(texts)>1 else None,
            source_ids=[documents[i]['id'] for i in sampled],definition='each sampled unit against all other sampled units; 0..100')
    summary=dict(schema='extended-lexical-v1',source_manifest_sha256=hashlib.sha256((ROOT/'manifest.json').read_bytes()).hexdigest(),
        distributions={'all':distribution_metrics(counts,bigrams),**{f:dict(tokens=sum(c.values()),entropy_bits=entropy(c.values())) for f,c in families.items()}},
        family_comparisons=[dict(p=a,q=b,**compare(families[a],families[b])) for a,b in itertools.combinations(families,2)],
        count_model=dict(model='smoothed unigram with one UNK bucket',alpha=.5,train_source_ids=train_ids,heldout_source_ids=[d['id'] for d,ts in heldout],split='sha256(source_id) modulo 5; no neural training'),vocabulary_growth=growth,growth_order='sources.jsonl order; no chronology or saturation claim',graph=graph,self_bleu=self_bleu,
        edit_candidate_scope='same first two characters, length difference <=1, edit distance <=1; not exhaustive',outputs=outputs)
    (ROOT/'extended-metrics.json').write_text(json.dumps(summary,indent=2,allow_nan=False))
    print(json.dumps(dict(status='verified run',documents=len(documents),artifacts=len(outputs),graph_nodes=graph['nodes'],graph_edges=graph['edges'])))

if __name__=='__main__':main()
