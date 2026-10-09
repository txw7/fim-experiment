"""Binding-aware graph export, witnessed template extraction, and typed probes.

All measurements name their projection. No coreference or semantic commutation
law is inferred from repeated spellings or graph similarity.
"""
from pathlib import Path
from dataclasses import asdict
from collections import Counter,deque
import json,hashlib,math,sqlite3,zlib
from calculus import *

ROOT=Path(__file__).resolve().parent
RUN=ROOT/'run'

def decode(x):
    def typ(t): return tuple(typ(a) for a in t) if isinstance(t,list) else t
    return Term(x['kind'],x['name'],typ(x['type']),tuple(decode(a) for a in x['args']),x['origin'])

def graph_export(term,object_id):
    nodes=[];edges=[];root=object_id+'#root'
    def edge(a,b,family,role):
        edges.append({'id':object_id+'#e'+str(len(edges)),'source':a,'target':b,'family':family,'role':role})
    def visit(t,address,env,stack,depth):
        nid=object_id+'#'+address
        nodes.append({'id':nid,'address':address,'kind':t.kind,'label':t.name,'type':type_text(infer(t,env)),'origin':t.origin,'structural_depth':depth})
        if t.kind=='var':
            found=next((b for name,b in reversed(stack) if name==t.name),None)
            if found: edge(nid,found,'bound-by','variable-resolution')
            else: nodes[-1]['external_parameter']=True
        if t.kind=='abstract':
            binder=nid+'/binder'
            nodes.append({'id':binder,'address':address+'/binder','kind':'binder','label':t.name,'type':type_text(t.type),'scope_root':nid+'/body','structural_depth':depth+1})
            edge(nid,binder,'declares','binder')
            stack=[*stack,(t.name,binder)];env={**env,t.name:t.type};roles=['body']
        elif t.kind=='call': roles=[role for role,typ in SIGNATURES[t.name][:-1]]
        elif t.kind=='apply': roles=['function','argument']
        else: roles=[]
        for role,arg in zip(roles,t.args):
            child=visit(arg,address+'/'+role,env,stack,depth+1)
            edge(nid,child,'structural-child',role)
        return nid
    visit(term,'root',free(term),[],0)
    by_id={n['id']:n for n in nodes}
    indegree=Counter(e['target'] for e in edges);outdegree=Counter(e['source'] for e in edges)
    for n in nodes:
        n['degree_by_family']={f:{'in':sum(e['target']==n['id'] and e['family']==f for e in edges),'out':sum(e['source']==n['id'] and e['family']==f for e in edges)} for f in ('structural-child','declares','bound-by')}
        n['branching_factor']=n['degree_by_family']['structural-child']['out']
    # No binder-to-body edge: scope is metadata, so binding references cannot
    # accidentally create body/use/binder cycles.
    queue=deque(n['id'] for n in nodes if indegree[n['id']]==0);seen=[]
    while queue:
        nid=queue.popleft();seen.append(nid)
        for e in edges:
            if e['source']==nid:
                indegree[e['target']]-=1
                if indegree[e['target']]==0: queue.append(e['target'])
    assert len(seen)==len(nodes)
    hypotheses=[]
    she=[n for n in nodes if n['kind']=='atom' and n['label'].startswith('she@')]
    if len(she)>=2:
        hypotheses.append({'family':'proposed-coreference','endpoints':[she[0]['id'],she[1]['id']],'status':'UNRESOLVED','basis':'Repeated pronoun; occurrence addresses do not prove referent identity.','admitted_edge':False})
    types=Counter(n['type'] for n in nodes)
    binding=[e for e in edges if e['family']=='bound-by']
    distances=[]
    for e in binding:
        use=by_id[e['source']]['address'].split('/');scope=by_id[by_id[e['target']]['scope_root']]['address'].split('/')
        assert use[:len(scope)]==scope
        e['scope_depth']=sum(1 for n in nodes if n['kind']=='binder' and (by_id[e['source']]['address']==by_id[n['scope_root']]['address'] or by_id[e['source']]['address'].startswith(by_id[n['scope_root']]['address']+'/')))
        # Binder declaration is a sibling of its body: count tree edges only.
        d=1+len(use)-len(scope)+1
        e['binder_tree_distance']=d;distances.append(d)
    raw=json.dumps(asdict(term),sort_keys=True).encode()
    metrics={'projection':'structural-child + declares for tree measures; bound-by measured separately','node_count':len(nodes),'edge_count':len(edges),'max_depth':max(n['structural_depth'] for n in nodes),'binding_use_count':len(binding),'mean_binding_tree_distance':sum(distances)/len(distances) if distances else None,'node_type_entropy_bits':-sum((v/len(nodes))*math.log2(v/len(nodes)) for v in types.values()),'serialized_compression_ratio':len(zlib.compress(raw))/len(raw),'directed_acyclic_all_admitted_edges':True,
             'uncomputed':{'pmi':'Needs corpus counts and a sampling unit.','type_distance':'No type-distance graph is declared.','source_mdd':'Implicit and generated positions lack a complete source-position mapping.','pagerank_betweenness':'Not implemented in this bounded increment.','temporal_trajectory':'No chronology is derived from temporal parameters.'}}
    return {'object_id':object_id,'root':root,'nodes':nodes,'edges':edges,'hypotheses':hypotheses,'metrics':metrics}

def canonical_binders(term):
    forbidden=set(free(term));prefix='__b'
    while any(n.startswith(prefix) for n in forbidden):prefix+='_' 
    counter=[0]
    def visit(t,env):
        if t.kind=='var':return var(env.get(t.name,t.name),t.type,t.origin)
        if t.kind=='abstract':
            name=prefix+str(counter[0]);counter[0]+=1
            return lam(var(name,t.type),visit(t.args[0],{**env,t.name:name}),t.origin)
        return Term(t.kind,t.name,t.type,tuple(visit(a,env) for a in t.args),t.origin)
    return visit(term,{})

def template_pair(left,right):
    a,b=canonical_binders(left),canonical_binders(right)
    fills=[]
    def unify(x,y):
        if alpha_key(x)==alpha_key(y):return x
        # This extraction deliberately generalizes entity leaves only. No
        # opaque whole-proposition placeholder can turn everything into a match.
        if not x.args and not y.args and infer(x,free(x))==infer(y,free(y))==E:
            name='subject_'+str(len(fills));fills.append((var(name,E),x,y));return fills[-1][0]
        if (x.kind,x.name,x.type,len(x.args))!=(y.kind,y.name,y.type,len(y.args)):
            raise ValueError('different constructor skeleton')
        return Term(x.kind,x.name,x.type,tuple(unify(p,q) for p,q in zip(x.args,y.args)),x.origin)
    body=unify(a,b)
    if not fills:raise ValueError('No varying entity position')
    template=body
    for parameter,_,_ in reversed(fills):template=lam(parameter,template)
    reconstructed=[]
    for column,original in ((1,left),(2,right)):
        application=template
        for fill in fills:application=apply(application,fill[column])
        result,steps=normalize(application)
        assert alpha_key(result)==alpha_key(original)
        reconstructed.append({'fill_terms':[asdict(f[column]) for f in fills],'application':asdict(application),'result':asdict(result),'reductions':steps,'alpha_equivalent_to_original':True})
    return {'term':asdict(template),'lisp':pretty(template),'type':type_text(infer(template)),'parameters':[{'name':p.name,'type':type_text(p.type)} for p,_,_ in fills],'reconstructions':reconstructed,'status':'WITNESSED_TEMPLATE','identity_claim':False}

def equivalence_probe(pid,label,left,right,assumptions):
    l,ls=normalize(left);r,rs=normalize(right)
    env={**free(left),**free(right)}
    lt=infer(left,env);rt=infer(right,env);assert lt==rt
    equal=alpha_key(l)==alpha_key(r)
    return {'id':pid,'label':label,'status':'EQUAL_UNDER_ALPHA_BETA' if equal else 'DISTINCT_ALPHA_BETA_NORMAL_FORMS','same_interface':type_text(lt),'common_context':{k:type_text(v) for k,v in env.items()},'left':{'term':asdict(left),'lisp':pretty(left),'normal_form':pretty(l),'reductions':ls},'right':{'term':asdict(right),'lisp':pretty(right),'normal_form':pretty(r),'reductions':rs},'commutes_under_enabled_laws':equal,'semantic_commutation':None,'laws':['alpha','capture-avoiding-beta','congruence'],'assumptions':assumptions}

def build():
    tower=json.loads((RUN/'tower.json').read_text());objects=tower['objects'];graphs={};templates=[];probes=[]
    for oid,obj in objects.items():
        if obj['kind']=='term':graphs[oid]=graph_export(decode(obj['payload']['term']),oid)
    by_branch={}
    for branch in tower['branches']:
        oid=branch['levels'][7];term=decode(objects[oid]['payload']['term'])
        def walk(t,path='root'):
            yield path,t
            roles=['body'] if t.kind=='abstract' else [r for r,typ in SIGNATURES[t.name][:-1]] if t.kind=='call' else ['function','argument'] if t.kind=='apply' else []
            for role,a in zip(roles,t.args):yield from walk(a,path+'/'+role)
        matches=[(address,t) for address,t in walk(term) if t.kind=='call' and t.name=='what' and t.args[0].args[0].kind=='call' and t.args[0].args[0].name=='was']
        assert len(matches)==2
        pattern=template_pair(matches[0][1],matches[1][1]);pattern.update(id='template:'+branch['id'],source_object=oid,occurrence_addresses=[a for a,t in matches],operation='typed-entity-leaf-anti-unification',authority='bounded construction calculus',parents=[oid])
        templates.append(pattern)
        # Reify the template as a higher-order operand, preserving the original
        # expanded tree and the two reconstruction witnesses as dependencies.
        by_branch[branch['id']]={'graph_object':oid,'template':pattern['id']}

    outer=next(b for b in tower['branches'] if b['id']=='when-copula');inner=next(b for b in tower['branches'] if b['id']=='when-right-state')
    get=lambda b,i:decode(objects[b['levels'][i]]['payload']['term'])
    probes.append(equivalence_probe('attachment-extent','Whole-copula versus right-state WHEN attachment',get(outer,3),get(inner,3),{'source_objects':[outer['levels'][3],inner['levels'][3]],'claim':'Compare existing complete contexts, not a raw permutation of operator names.','source_interpretation':'UNSELECTED'}))

    base=get(outer,2)
    # Independent replacements operate on exact source-subject positions.
    a,b=var('a',E),var('b',E);x,y=var('x',E),var('y',E)
    def expose(t):
        if t.kind=='atom' and t.name=='she@1':return a
        if t.kind=='atom' and t.name=='he@5':return b
        return Term(t.kind,t.name,t.type,tuple(expose(q) for q in t.args),t.origin)
    context=expose(base)
    xy=substitute(substitute(context,'a',x),'b',y)
    yx=substitute(substitute(context,'b',y),'a',x)
    probes.append(equivalence_probe('independent-substitutions','Independent entity-port substitutions',xy,yx,{'operation_left':['a:=x','b:=y'],'operation_right':['b:=y','a:=x'],'side_conditions':['a != b','a not free(y)','b not free(x)'],'parameters':{'a':E,'b':E,'x':E,'y':E},'evidence_class':'GENERATED_CONSTRUCTION_PROBE','source_context':outer['levels'][2]}))
    nodes=dict((address,t) for address,t in walk_local(base))
    left=next(t for address,t in nodes.items() if t.kind=='call' and t.name=='what' and t.args[0].args[0].name=='was')
    right=next(t for address,t in nodes.items() if t.kind=='call' and t.name=='what' and t.args[0].args[0].name=='is')
    lr=substitute(substitute(base,'h',left),'h',right)
    rl=substitute(substitute(base,'h',right),'h',left)
    probes.append(equivalence_probe('same-slot-overwrite','Competing substitutions into the same open complement',lr,rl,{'operation_left':['h:=source-left-description','h:=source-right-description'],'operation_right':['h:=source-right-description','h:=source-left-description'],'evidence_class':'GENERATED_CONSTRUCTION_PROBE','claim':'Ordinary substitution removes h on the first replacement; later substitution has no remaining h to replace.'}))
    # Negative test for the independence side condition: b occurs in a's fill.
    dep_lr=substitute(substitute(context,'a',b),'b',x)
    dep_rl=substitute(substitute(context,'b',x),'a',b)
    dep=equivalence_probe('dependent-substitutions','Dependent substitutions fail the independence condition',dep_lr,dep_rl,{'side_condition_violated':'b is free in replacement a:=b','operations':[['a:=b','b:=x'],['b:=x','a:=b']]})
    assert not dep['commutes_under_enabled_laws'];probes.append(dep)
    probes.append({'id':'raw-when-what','label':'Raw WHEN / WHAT operator swap','status':'NOT_COMPOSABLE_AS_GIVEN','commutes_under_enabled_laws':None,'semantic_commutation':None,'reason':'Neither name denotes a unary endomorphism over a common declared type. An addressed, well-typed contextual rewrite is required.','signatures':{k:v for k,v in SIGNATURES.items() if k in ('when-operator','what')}})
    probes.append({'id':'what-what-identity','label':'Repeated WHAT abstractions / repeated p spelling','status':'UNPROVEN_IDENTITY_OR_COMMUTATION','commutes_under_enabled_laws':None,'semantic_commutation':None,'reason':'Independent binding identities do not license copular argument exchange or referent identity.'})
    probes.append({'id':'anchor-fixed-point','label':'Anchor WHAT as a proposed fixed point','status':'MISSING_TRANSFORMATION','commutes_under_enabled_laws':None,'semantic_commutation':None,'reason':'A fixed-point claim needs a declared transformation F and a witnessed equation F(x)=x. No such transformation is supplied.'})
    assert probes[1]['commutes_under_enabled_laws'] and not probes[2]['commutes_under_enabled_laws']
    result={'graphs':graphs,'templates':templates,'probes':probes,'by_branch':by_branch,'schema':{'relation_families':['structural-child','declares','bound-by','proposed-coreference','witnessed-equivalence'],'hypotheses_are_not_admitted_edges':True,'identity_from_name_or_occurrence_address':False},'summary':{'exported_term_graphs':len(graphs),'witnessed_templates':len(templates),'successful_reconstructions':sum(len(t['reconstructions']) for t in templates),'probes_by_status':dict(Counter(p['status'] for p in probes))},'native_admission':False}
    (RUN/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    write_db(result)
    lines=['Binding-aware tower analysis','',json.dumps(result['summary'],indent=2),'','Shared template:',templates[0]['lisp'],'','Each instance is reconstructed by typed application and alpha/beta normalization.','No subject identity or doubled-binder identity is asserted.','','Probes:']
    for p in probes:lines += [p['id']+': '+p['status'],p.get('reason','')]
    (RUN/'analysis.txt').write_text('\n'.join(lines)+'\n')
    # Scope regression: matching spellings resolve to separate lexical binders.
    g=graphs[outer['levels'][7]]
    p_binders=[n for n in g['nodes'] if n['kind']=='binder' and n['label']=='p']
    assert len(p_binders)==2 and p_binders[0]['id']!=p_binders[1]['id']
    assert not any(e['family']=='identity' for e in g['edges'])
    uses=[e for e in g['edges'] if e['family']=='bound-by' and e['target'] in {n['id'] for n in p_binders}]
    assert len(uses)==2 and len({e['target'] for e in uses})==2
    print(json.dumps(result['summary'],indent=2))
    return result

def walk_local(t,path='root'):
    yield path,t
    for i,a in enumerate(t.args):yield from walk_local(a,path+'/'+str(i))

def write_db(data):
    db=sqlite3.connect(RUN/'tower-analysis.sqlite');db.execute('PRAGMA foreign_keys=ON')
    db.executescript('''
    CREATE TABLE IF NOT EXISTS graphs(id TEXT PRIMARY KEY, payload_json TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS nodes(id TEXT PRIMARY KEY, graph_id TEXT NOT NULL REFERENCES graphs(id), kind TEXT NOT NULL, payload_json TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS edges(id TEXT PRIMARY KEY, graph_id TEXT NOT NULL REFERENCES graphs(id), source_id TEXT NOT NULL REFERENCES nodes(id), target_id TEXT NOT NULL REFERENCES nodes(id), family TEXT NOT NULL, role TEXT NOT NULL, payload_json TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS hypotheses(id TEXT PRIMARY KEY, graph_id TEXT NOT NULL REFERENCES graphs(id), status TEXT NOT NULL, payload_json TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS templates(id TEXT PRIMARY KEY, source_object TEXT NOT NULL REFERENCES graphs(id), payload_json TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS probes(id TEXT PRIMARY KEY, status TEXT NOT NULL, commutes_under_enabled_laws INTEGER, payload_json TEXT NOT NULL);
    ''')
    with db:
        for gid,g in data['graphs'].items():
            db.execute('INSERT OR REPLACE INTO graphs VALUES (?,?)',(gid,json.dumps(g['metrics'])))
            for n in g['nodes']:db.execute('INSERT OR REPLACE INTO nodes VALUES (?,?,?,?)',(n['id'],gid,n['kind'],json.dumps(n)))
            for e in g['edges']:db.execute('INSERT OR REPLACE INTO edges VALUES (?,?,?,?,?,?,?)',(e['id'],gid,e['source'],e['target'],e['family'],e['role'],json.dumps(e)))
            for i,h in enumerate(g['hypotheses']):db.execute('INSERT OR REPLACE INTO hypotheses VALUES (?,?,?,?)',(gid+'#hypothesis'+str(i),gid,h['status'],json.dumps(h)))
        for t in data['templates']:db.execute('INSERT OR REPLACE INTO templates VALUES (?,?,?)',(t['id'],t['source_object'],json.dumps(t)))
        for p in data['probes']:db.execute('INSERT OR REPLACE INTO probes VALUES (?,?,?,?)',(p['id'],p['status'],p.get('commutes_under_enabled_laws'),json.dumps(p)))
    assert db.execute('PRAGMA foreign_key_check').fetchall()==[]
    assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    db.close()

if __name__=='__main__':build()
