"""Unscaffolded source-grounded hypothesis search. No model law admission."""
import copy,concurrent.futures,importlib.util,json,re,subprocess,sys,time
from pathlib import Path
sys.path.insert(0,'/home/user0/semalg-flow-viewer/native-lift-v1')
from worker import NATIVE,save,atomic_text,sha
from observers import post
from candidate_bridge import sexp
HERE=Path(__file__).parent

def obj_schema(properties):return dict(type='object',properties=properties,required=list(properties),additionalProperties=False)
STR={'type':'string'};ARR=lambda x:dict(type='array',items=x)
NODE=obj_schema(dict(id=STR,kind=dict(type='string',enum=['entity','operator','proposition','network','position','binder']),type=STR,anchors=ARR(STR),members=ARR(STR),license=STR))
REL=obj_schema(dict(id=STR,family=dict(type='string',enum=['argument','binding','scope','attachment','inference','enclosure','lift']),constitution=STR,ends=ARR(obj_schema(dict(role=STR,target=STR)))))
CAND=obj_schema(dict(id=STR,reading=STR,objects=ARR(NODE),relations=ARR(REL)))
SCHEMA=obj_schema(dict(candidates=ARR(CAND),unresolved=ARR(STR)))


def sources():
 yield 'recursive','what she was when he was where they were where she was when it happened',dict(origin='literal user construction from conversation')
 p=Path('/home/user0/.local/state/turn-transport/aristotle-operator-examples-v1/results.json');e=next(e for e in json.loads(p.read_text())['examples'] if 'as much clarity' in e['source'])
 yield 'comparison',e['source'],dict(path=str(p),sha256=sha(p.read_bytes()),original_ref=e['source_ref'])
 p=Path('/home/user0/.local/state/turn-transport/aristotle-logic-pilot-v1/ethics-source.json');u=json.loads(p.read_text())['units'];selected=u[16:19]
 yield 'inference','\n'.join(x['text'] for x in selected),dict(path=str(p),sha256=sha(p.read_bytes()),units=selected,joining='newlines between unchanged extracted units; XML tree references retained')


def tokens(text):return [dict(id='t'+str(i),text=m.group(),begin=m.start(),end=m.end()) for i,m in enumerate(re.finditer(r'\w+(?:[-\u2019\']\w+)*|[^\w\s]',text))]


def check(candidate,occurrences):
 nodes=candidate['objects'];relations=candidate['relations'];ids=[x['id'] for x in nodes+relations]
 errors=[];obligations=[]
 if len(nodes)>64 or len(relations)>128:errors.append('object/incidence bound exceeded')
 if len(ids)!=len(set(ids)):errors.append('duplicate identity')
 known=set(ids);anchors={t['id'] for t in occurrences};byid={o['id']:o for o in nodes}
 for o in nodes:
  if not set(o['anchors'])<=anchors:errors.append('unknown source anchor '+o['id'])
  if not o['anchors'] and (o['kind'] not in ('position','binder') or not o['license']):errors.append('unlicensed implicit object '+o['id'])
  if not set(o['members'])<=known:errors.append('dangling interior '+o['id'])
  if o['members'] and o['kind']!='network':errors.append('non-network interior '+o['id'])
  if not o['anchors']:obligations.append(dict(subject=o['id'],requirement='grammatical-position license',claimed=o['license']))
  if o['kind']=='operator':obligations.append(dict(subject=o['id'],requirement='operator constitution',claimed=o['license'],hypothesized_type=o['type']))
 for r in relations:
  if any(e['target'] not in known for e in r['ends']):errors.append('dangling relation operand '+r['id'])
  obligations.append(dict(subject=r['id'],requirement=r['family']+' constitution',claimed=r['constitution']))
 def walk(node,stack):
  if node in stack:raise ValueError('containment cycle')
  for m in byid.get(node,{}).get('members',[]):walk(m,stack|{node})
 try:
  for n in byid:walk(n,set())
 except ValueError as e:errors.append(str(e))
 # Backward obligations are generated from actual higher-order candidate incidences.
 backward=[]
 for r in relations:
  if r['family'] in ('binding','inference','lift','attachment'):
   for end in r['ends']:
    backward.append(dict(parent=r['id'],child=end['target'],role=end['role'],requires='establish typed interface and '+('binding locality' if r['family']=='binding' else 'source license'),status='OPEN'))
 return dict(status='REJECTED' if errors else 'STRUCTURALLY_REVIEWABLE',errors=errors,obligations=obligations,backward_goals=backward,semantic_admission='NOT_RUN')


def propose(path,text,occurrences,feedback=None):
 started=time.monotonic()
 system='Construct competing semantic graph hypotheses from unchanged source occurrences. No operator inventory or topology is supplied. Propose at most TWO small different analyses, each at most 10 objects and 10 relations. Choose operator names, types, grammatical positions, roles, binding, scope and network boundaries. Objects have source token IDs; missing grammatical positions may have no anchors ONLY with an explicit named grammatical construction license. No invented lexical referents. Networks retain member identities and may be operands of higher relations. Relation endpoints may reference relations. Different readings should differ in structure, not just labels. Separate argument, binding, attachment and scope. Every constitution/license is a CLAIM requiring native checking, not proof. On feedback, address narrower backward obligations and preserve viable alternatives; do not silently resolve source ambiguity. Do not summarize. Token anchors are IDs, never regenerate offsets.'
 state=dict(source=text,occurrences=occurrences,available_native_mechanisms=['opaque occurrence formation','partial graph/region/incidence holes','bounded graph search','region contraction/expansion'],missing_native_meanings=['arbitrary lexical/grammatical operator constitution admission','wh gap licensing','temporal operator disambiguation','natural-language inference proof'],feedback=feedback,limits=dict(max_total_alternatives=4,max_expansions=100))
 body=dict(model='local',messages=[dict(role='system',content=system),dict(role='user',content=json.dumps(state,separators=(',',':')))],temperature=0,max_tokens=1900,chat_template_kwargs={'enable_thinking':False},response_format={'type':'json_schema','json_schema':dict(name='construction_programs',strict=True,schema=SCHEMA)})
 save(path/'request.json',body)
 try:
  response=post('http://127.0.0.1:8088/v1/chat/completions',body);save(path/'response.json',response)
  if response['choices'][0]['finish_reason']!='stop':raise ValueError('token budget exhausted; partial response retained')
  result=dict(status='COMPLETED',proposal=json.loads(response['choices'][0]['message']['content']))
 except Exception as e:result=dict(status='FAILED',error=str(e),response_error=e.read().decode(errors='replace') if hasattr(e,'read') else None)
 result['latency_seconds']=round(time.monotonic()-started,3);save(path/'result.json',result);return result


def observe(path,text,candidates,checks):
 state=dict(source=text,candidates=candidates,checks=checks,authority='Model alternatives only. Missing grammatical laws remain open.')
 question={'network':dict(type='choice',instructions='Compare whole source-grounded candidate graphs, including introduced positions, binding and higher-order operands. Which candidate has the best source support? Probabilities do not discharge laws.',criteria={**{c['id']:c['reading'] for c in candidates},'unresolved':'Source/law evidence does not determine a unique graph.'})}
 if not candidates:return dict(laya=dict(status='NOT_RUN'),jev=dict(status='NOT_RUN'))
 def call(provider):
  started=time.monotonic()
  try:
   if provider=='jev':
    client=Path('/home/user0/research-gold-disrpt/corpusGraph/scripts/jev_systemone.py');spec=importlib.util.spec_from_file_location('jev_search',client);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    save(path/'jev-request.json',dict(state=state,questions=question));response=m.decide(json.dumps(state),question);answer=response.get('answers',{})
   else:
    # Narrow local diagnostic on the first actual backward obligation, within Laya's context budget.
    goals=[g for v in checks.values() for g in v['backward_goals']];goal=goals[0] if goals else dict(requires='licensed expression construction')
    local=dict(source=text,goal=goal,candidate_readings=[c['reading'] for c in candidates],instruction='Does source establish this exact dependency, conflict with it, or leave it unresolved?')
    q={'dependency':dict(type='choice',criteria={'supported':'Exact proposed dependency is source-supported.','unsupported':'It conflicts with source.','unresolved':'Insufficient binding, role or construction evidence.'})}
    body=dict(model='english',state=json.dumps(local,separators=(',',':')),questions=q);save(path/'laya-request.json',body);response=post('http://127.0.0.1:8091/v1/systemone',body);answer=response.get('answers',{})
   save(path/(provider+'-response.json'),response)
   if response.get('usage',{}).get('truncated') or response.get('usage',{}).get('state_tokens_dropped'):raise ValueError('truncated classifier context')
   result=dict(status='COMPLETED',answers=answer)
  except Exception as e:result=dict(status='FAILED',error=str(e))
  result.update(latency_seconds=round(time.monotonic()-started,3),admission='NOT_AUTHORIZED');save(path/(provider+'.json'),result);return result
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  futures={p:pool.submit(call,p) for p in ('laya','jev')};return {p:f.result() for p,f in futures.items()}


def case(root,name,text,origin):
 path=root/name;occ=tokens(text);save(path/'source.json',dict(text=text,sha256=sha(text.encode()),origin=origin));save(path/'occurrences.json',occ)
 first=propose(path/'initial',text,occ);candidates=first.get('proposal',{}).get('candidates',[])[:2]
 for i,c in enumerate(candidates):c['id']='initial-'+str(i)
 checks={c['id']:check(c,occ) for c in candidates};save(path/'initial/candidates.json',candidates);save(path/'initial/checks.json',checks)
 observations=observe(path/'observers',text,candidates,checks);save(path/'observers/results.json',observations)
 # Bounded backward revision consumes exact prior candidate structures and diagnostics.
 second=propose(path/'feedback',text,occ,dict(candidates=candidates,checks=checks,observations=observations))
 later=second.get('proposal',{}).get('candidates',[])[:2]
 for i,c in enumerate(later):c['id']='feedback-'+str(i)
 candidates+=later
 allchecks={c['id']:check(c,occ) for c in candidates};save(path/'candidates.json',candidates);save(path/'checks.json',allchecks)
 report=dict(source=name,candidates=len(candidates),initial_status=first['status'],feedback_status=second['status'],shape_signatures=[dict(candidate=c['id'],objects=len(c['objects']),relations=len(c['relations']),kinds=sorted({o['kind'] for o in c['objects']}),network_operands=sum(e['target'] in {o['id'] for o in c['objects'] if o['kind']=='network'} for r in c['relations'] for e in r['ends'])) for c in candidates],native_semantic_admission='NOT_RUN',observations=observations)
 save(path/'report.json',report);print(json.dumps(dict(source=name,candidates=len(candidates),initial=first['status'],feedback=second['status'])),flush=True);return report

if __name__=='__main__':
 root=HERE/'runs'/str(time.time_ns());root.mkdir(parents=True,mode=0o700);pins={str(Path(__file__)):sha(Path(__file__).read_bytes())};save(root/'pins.json',pins)
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  futures=[pool.submit(case,root,*s) for s in sources()];reports=[f.result() for f in futures]
 assert all(sha(Path(p).read_bytes())==h for p,h in pins.items())
 save(root/'results.json',reports);atomic_text(HERE/'latest.txt',str(root)+'\n');print(str(root))
