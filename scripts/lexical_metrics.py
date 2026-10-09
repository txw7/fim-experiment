"""Count-derived measures; all associations share a directed window-event population."""
import collections, math, zlib

def association(c, a, b, n):
    p, pa, pb = c/n, a/n, b/n
    pmi = math.log2(p/(pa*pb))
    cells = (c, a-c, b-c, n-a-b+c)
    expected = (a*b/n, a*(n-b)/n, (n-a)*b/n, (n-a)*(n-b)/n)
    llr = 2*sum(x*math.log(x/e) for x,e in zip(cells,expected) if x and e)
    confidence = c/a
    return dict(pmi=pmi, ppmi=max(0,pmi), npmi=pmi/-math.log2(p) if p<1 else None,
                lift=p/(pa*pb), confidence=confidence,
                conviction=(1-pb)/(1-confidence) if confidence<1 else None,
                logdice=14+math.log2(2*c/(a+b)), llr=llr,
                source_marginal=a, target_marginal=b, event_population=n)

def entropy(values):
    n=sum(values)
    return -sum((c/n)*math.log2(c/n) for c in values if c) if n else 0

def profiles(documents, token_pattern):
    counts=collections.defaultdict(collections.Counter)
    lengths=collections.Counter(); positions=collections.defaultdict(list); summaries=[]
    for doc in documents:
        tokens=[m.group().casefold() for m in token_pattern.finditer(doc['text'])]
        n=len(tokens); v=len(set(tokens)); family=doc['family']; lengths[family]+=n
        local=collections.defaultdict(list)
        for i,t in enumerate(tokens): counts[t][family]+=1; local[t].append(i)
        for t,ps in local.items(): positions[t].extend(b-a for a,b in zip(ps,ps[1:]))
        raw=doc['text'].encode()
        summaries.append(dict(source_id=doc['id'], tokens=n, types=v, ttr=v/n if n else 0,
            rttr=v/math.sqrt(n) if n else 0, cttr=v/math.sqrt(2*n) if n else 0,
            entropy_bits=entropy(collections.Counter(tokens).values()),
            zlib_ratio=len(zlib.compress(raw))/len(raw) if raw else None))
    terms=[]
    for t,c in counts.items():
        gaps=positions[t]; mean=sum(gaps)/len(gaps) if gaps else None
        terms.append(dict(term=t, family_counts=dict(c), family_entropy_bits=entropy(c.values()),
            family_rates={f:c[f]/n for f,n in lengths.items() if n},
            within_document_gap_samples=len(gaps), gap_mean=mean,
            gap_sd=math.sqrt(sum((x-mean)**2 for x in gaps)/len(gaps)) if gaps else None))
    return summaries,terms

def keyword_graph(pairs,min_count):
    edges=[]; adjacency=collections.defaultdict(dict)
    for (a,b),c in pairs.items():
        if a>=b or c<min_count: continue
        edges.append(dict(source=a,target=b,count=c)); adjacency[a][b]=c; adjacency[b][a]=c
    n=len(adjacency); rank={a:1/n for a in adjacency} if n else {}; weighted={a:sum(v.values()) for a,v in adjacency.items()}
    for _ in range(30):
        new={a:0.15/n for a in adjacency}
        for a,neighbors in adjacency.items():
            for b,w in neighbors.items(): new[b]+=0.85*rank[a]*w/weighted[a]
        rank=new
    nodes=[]
    for a,neighbors in adjacency.items():
        ns=set(neighbors); k=len(ns)
        links=sum(len(ns.intersection(adjacency[b])) for b in ns)
        nodes.append(dict(id=a,degree=k,weighted_degree=weighted[a],pagerank=rank[a],
                          clustering=links/(k*(k-1)) if k>1 else 0))
    return dict(schema='lexical-network-v1', directed=False, self_loops=False,
        edge_definition='within-document next-window co-occurrence, minimum count applied',
        nodes=nodes,edges=edges,authority='lexical association, not logical entailment')
