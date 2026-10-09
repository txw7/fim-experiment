"""Typed construction contract, source immutable outside model output; sequential streaming calls."""
import json,time,urllib.request,sys,hashlib
from pathlib import Path
import search as b
import expanded as e
ROOT=Path(__file__).parent
S={'type':'string'}
def arr(x):return {'type':'array','items':x}
obj=b.obj_schema
PORT=obj({'id':S,'role':S,'value_type':S,'filler':S})
APP=obj({'id':S,'operator':S,'anchors':arr(S),'construction':S,'ports':arr(PORT),'result_type':S})
POSITION=obj({'id':S,'role':S,'value_type':S,'license':S})
BIND=obj({'id':S,'binder':S,'position':S,'domain':S,'license':S})
NET=obj({'id':S,'members':arr(S),'imports':arr(S),'exports':arr(S)})
REL=obj({'id':S,'family':S,'roles':arr(obj({'role':S,'target':S})),'license':S})
SCHEMA=obj({'reading':S,'applications':arr(APP),'positions':arr(POSITION),'bindings':arr(BIND),'networks':arr(NET),'relations':arr(REL),'unresolved':arr(S)})

def validate(c,text):
 ts=b.tokens(text);lex={t['id'] for t in ts};apps={x['id']:x for x in c['applications']};positions={x['id']:x for x in c['positions']};nets={x['id']:x for x in c['networks']};ports={p['id']:(a,p) for a in c['applications'] for p in a['ports']};rels={x['id']:x for x in c['relations']};binds={x['id']:x for x in c['bindings']}
 ids=[t['id'] for t in ts]+[a['id'] for k in ('applications','positions','bindings','networks','relations') for a in c[k]]+[p['id'] for a in c['applications'] for p in a['ports']];known=set(ids);errors=[];obligations=[]
 if len(ids)!=len(known):errors.append('duplicate identity')
 for a in c['applications']:
  if not set(a['anchors'])<=lex:errors.append('unknown operator anchor '+a['id'])
  if not a['anchors']:errors.append('operator application lacks source anchor '+a['id'])
  if not a['ports']:errors.append('application lacks argument interface '+a['id'])
  if not a['result_type']:errors.append('application lacks result type '+a['id'])
  obligations.append({'subject':a['id'],'law':a['construction'],'status':'UNREGISTERED'})
  for p in a['ports']:
   if p['filler'] not in known:errors.append('unresolved port filler '+p['id'])
   if p['filler']==a['id']:errors.append('self argument '+p['id'])
   if not p['value_type'] or not p['role']:errors.append('untyped port '+p['id'])
 for pos in c['positions']:
  if not pos['license']:errors.append('unlicensed position '+pos['id'])
  obligations.append({'subject':pos['id'],'law':pos['license'],'status':'UNREGISTERED'})
 for x in c['bindings']:
  if x['binder'] not in known or x['position'] not in positions or x['domain'] not in apps.keys()|nets.keys():errors.append('invalid binding endpoints '+x['id'])
 for n in c['networks']:
  if not set(n['members']+n['imports']+n['exports'])<=known:errors.append('dangling network interface '+n['id'])
  if not n['exports']:errors.append('network has no output interface '+n['id'])
 for r in c['relations']:
  if any(x['target'] not in known for x in r['roles']):errors.append('dangling relation '+r['id'])
 used={t for a in c['applications'] for t in a['anchors']}|{p['filler'] for a in c['applications'] for p in a['ports']}|{x['target'] for r in c['relations'] for x in r['roles']}
 missing=[t['id'] for t in ts if t['id'] not in used]
 operators=[t['id'] for t in ts if t['text'] in ('what','when','where') and not any(t['id'] in a['anchors'] for a in c['applications'])]
 # References must not create hidden recursive containment/application cycles.
 edges={a['id']:[p['filler'] for p in a['ports']] for a in c['applications']};edges.update({n['id']:n['members'] for n in c['networks']})
 def walk(x,stack):
  if x in stack:raise ValueError('application/containment cycle')
  for y in edges.get(x,[]):walk(y,stack|{x})
 try:
  for x in edges:walk(x,set())
 except ValueError as ex:errors.append(str(ex))
 return {'errors':errors,'uncovered_occurrences':missing,'uninterpreted_operator_occurrences':operators,'law_obligations':obligations,'structural_gate':not errors and not operators and bool(c['applications']) and bool(c['networks']),'semantic_admission':'NOT_RUN','source_preservation':'IMMUTABLE_EXTERNAL_SUBSTRATE'}

def call(path,text,feedback=None):
 system='Construct a grammatical hypothesis with typed operator applications and interfaces. Source tokens are immutable external occurrences: do not regenerate them. References may name source token IDs or declared applications, ports, positions, bindings, networks and relations. Choose the operator names, grammatical analysis and types yourself; no intended reading is supplied. Applications must have anchored source operators, typed argument ports and result types. Ports point to exact occurrences or constructed results; use licensed grammatical positions for absent arguments rather than invented words. Bindings identify an actual position and its domain. Networks preserve member identities and expose typed results through application/port references. Separate predicate arguments, binding, scope and attachment. A source fragment may be incomplete or ambiguous: retain that explicitly. Do not fabricate a completed interpretation or native law. Each license is a hypothesis requiring independent native verification. Account for every source occurrence, especially what/when/where. Return one compact candidate: usually fewer than 8 applications and 3 networks. If no interpretation is justified explain it in unresolved rather than mislabeling simple adjacency as binding.'
 body={'model':'local','messages':[{'role':'system','content':system},{'role':'user','content':json.dumps({'source':text,'occurrences':b.tokens(text),'feedback':feedback},separators=(',',':'))}],'temperature':0,'max_tokens':2600,'stream':True,'chat_template_kwargs':{'enable_thinking':False},'response_format':{'type':'json_schema','json_schema':{'name':'typed_construction','strict':True,'schema':SCHEMA}}}
 b.save(path/'request.json',body);path.mkdir(parents=True,exist_ok=True);chunks=[];finish=None;start=time.monotonic()
 try:
  req=urllib.request.Request('http://127.0.0.1:8088/v1/chat/completions',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
  with urllib.request.urlopen(req,timeout=45) as response, (path/'stream.jsonl').open('w') as journal:
   for line in response:
    if time.monotonic()-start>180:raise TimeoutError('generation exceeded 180-second bound')
    if not line.startswith(b'data: '):continue
    raw=line[6:].decode().strip()
    if raw=='[DONE]':break
    event=json.loads(raw);journal.write(json.dumps(event)+'\n');journal.flush()
    for choice in event.get('choices',[]):
     delta=choice.get('delta',{}).get('content')
     if delta:chunks.append(delta)
     if choice.get('finish_reason'):finish=choice['finish_reason']
  content=''.join(chunks);(path/'output.txt').write_text(content)
  if finish!='stop':raise ValueError('incomplete stream '+str(finish))
  c=json.loads(content);result={'status':'COMPLETED','candidate':c,'checks':validate(c,text)}
 except Exception as ex:result={'status':'FAILED','error':str(ex)};(path/'partial.txt').write_text(''.join(chunks))
 result['seconds']=round(time.monotonic()-start,2);b.save(path/'result.json',result);return result

if __name__=='__main__':
 root=ROOT/'typed-local-runs'/str(time.time_ns());root.mkdir(parents=True,mode=0o700);print(root,flush=True)
 b.save(root/'executed-source.json',{'code':Path(__file__).read_text(),'sha256':b.sha(Path(__file__).read_bytes())})
 results={}
 for name,text in [('what','what she was'),('when','when he was'),('where','where they were')]:
  b.save(root/name/'source.json',{'text':text,'occurrences':b.tokens(text),'sha256':b.sha(text.encode())})
  a=call(root/name/'initial',text)
  d=call(root/name/'repair',text,{'candidate':a['candidate'],'checks':a['checks']}) if a['status']=='COMPLETED' else {'status':'NOT_RUN'}
  results[name]={'source':text,'initial':a,'repair':d};b.save(root/'results.json',results);print(name,a['status'],d['status'],flush=True)
 b.atomic_text(ROOT/'typed-local-latest.txt',str(root)+'\n');print('DONE',root,flush=True)
