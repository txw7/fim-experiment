"""Immutable lexical substrate plus bounded local construction/repair/composition probe."""
import json,time,copy,concurrent.futures
from pathlib import Path
import expanded as e
import search as b
ROOT=Path(__file__).parent
SCHEMA=copy.deepcopy(e.SCHEMA)
SCHEMA['properties']['candidates']['items']['properties']['objects']['items']['properties']['kind']['enum'].append('occurrence')
SCHEMA['properties']['candidates']['items']['properties']['objects']['maxItems']=64

def substrate(text):
 return [{'id':'n'+str(i),'kind':'occurrence','type':'lexical-occurrence','anchors':[t['id']],'members':[],'license':'literal source occurrence'} for i,t in enumerate(b.tokens(text))]

def verify(c,text):
 occ=b.tokens(text);fixed=substrate(text);byid={o['id']:o for o in c['objects']};v=e.validate(c,occ)
 v['substrate_errors']=[f"immutable occurrence altered or missing: {o['id']}" for o in fixed if byid.get(o['id'])!=o]
 # Coverage concerns semantic use, not copying the permanent lexical layer.
 lexical={o['id'] for o in fixed};used={e['target'] for r in c['relations'] for e in r['ends']}|{m for o in c['objects'] if o['id'] not in lexical for m in o['members']}
 derivedanchors={a for o in c['objects'] if o['id'] not in lexical for a in o['anchors']}
 missing=[t for i,t in enumerate(occ) if 'n'+str(i) not in used and t['id'] not in derivedanchors]
 v['uninterpreted_occurrences']=missing
 v['uninterpreted_operators']=[t for t in missing if t['text'].lower() in ('what','when','where')]
 v['source_preserved']=not v['substrate_errors'];v['complete_operator_coverage']=not v['uninterpreted_operators']
 v['construction_obligations']=['No derived operator/application, position, binder, proposition or network result is declared. Lexical links alone do not satisfy the construction contract.'] if not any(o['kind'] in ('operator','position','binder','proposition','network') for o in c['objects']) else []
 v['semantic_status']='UNVERIFIED_LICENSES';return v

def ask(path,text,feedback=None,components=None):
 fixed=substrate(text)
 system='Propose ONE grammatical operator setup against unchanged source. The supplied lexical objects are immutable: copy each exactly once, unchanged, into objects. New IDs start after the last supplied n-ID. Preserve lexical occurrences as addressable operands, not replacements. Do not summarize or merely nest the words. Propose argument positions, operator applications, binding, attachment, scope and output interfaces appropriate to your chosen analysis; retain ambiguity. Absent grammatical positions require named construction licenses; these are claims, not proofs. Only networks may have members; all references must resolve; no containment cycles. Groupings retain lexical members. Relation endpoints can be lexical occurrences, derived objects, or other relations. Do not invent lexical referents. Every what/when/where occurrence must be interpreted by a proposed construction or explicitly remain unresolved. For composition, supplied component graphs are evidence, not admitted meanings: preserve interiors and identities if reused, and expose incompatible components as obligations. Do not claim native admission. On repair address exact errors; dropping operators is not a repair.'
 body={'model':'local','messages':[{'role':'system','content':system},{'role':'user','content':json.dumps({'source':text,'occurrences':b.tokens(text),'immutable_objects':fixed,'feedback':feedback,'components':components},separators=(',',':'))}],'temperature':0,'max_tokens':6000,'chat_template_kwargs':{'enable_thinking':False},'response_format':{'type':'json_schema','json_schema':{'name':'local_construction','strict':True,'schema':SCHEMA}}}
 b.save(path/'request.json',body);start=time.monotonic()
 try:
  response=b.post('http://127.0.0.1:8088/v1/chat/completions',body);b.save(path/'response.json',response)
  if response['choices'][0]['finish_reason']!='stop':raise ValueError('incomplete response')
  c=json.loads(response['choices'][0]['message']['content'])['candidates'][0];result={'status':'COMPLETED','candidate':c,'checks':verify(c,text)}
 except Exception as ex:result={'status':'FAILED','error':str(ex)}
 result['seconds']=round(time.monotonic()-start,2);b.save(path/'result.json',result);return result

def case(root,name,text):
 p=root/name;b.save(p/'source.json',{'text':text,'sha256':b.sha(text.encode())});b.save(p/'substrate.json',substrate(text));a=ask(p/'initial',text)
 if a['status']=='COMPLETED':
  # Use one actual nontrivial relation rather than the first lexical relation where possible.
  c=a['candidate'];obs=e.observers(p/'observers',text,c);feedback={'candidate':c,'checks':a['checks'],'laya':obs};d=ask(p/'repair',text,feedback)
 else:d={'status':'NOT_RUN'}
 result={'source':text,'initial':a,'repair':d};b.save(p/'results.json',result);print(name,a['status'],d['status'],flush=True);return name,result

if __name__=='__main__':
 root=ROOT/'local-runs'/str(time.time_ns());root.mkdir(parents=True,mode=0o700);print(root,flush=True)
 b.save(root/'pins.json',{str(Path(__file__)):b.sha(Path(__file__).read_bytes()),str(Path(e.__file__)):b.sha(Path(e.__file__).read_bytes()),str(Path(b.__file__)):b.sha(Path(b.__file__).read_bytes())})
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  fs=[pool.submit(case,root,n,t) for n,t in [('what','what she was'),('when','when he was'),('where','where they were')]];results=dict(f.result() for f in fs)
 # No component is silently promoted to checked meaning.
 eligible={n:d['repair'] for n,d in results.items() if d['repair'].get('status')=='COMPLETED' and not d['repair']['checks']['errors'] and d['repair']['checks']['source_preserved'] and d['repair']['checks']['complete_operator_coverage'] and not d['repair']['checks']['construction_obligations']}
 b.save(root/'composition-gate.json',{'eligible_structural_proposals':list(eligible),'semantic_admission':'NOT_RUN','licensed_native_components':[]})
 if len(eligible)==3:
  text='what she was when he was where they were';composed=ask(root/'composition',text,components={n:d['candidate'] for n,d in eligible.items()})
 else:composed={'status':'BLOCKED','reason':'Local proposals fail structural/source/operator-preservation gates; no checked components to compose.'}
 b.save(root/'composition.json',composed);b.save(root/'results.json',results);b.atomic_text(ROOT/'local-latest.txt',str(root)+'\n');print('DONE',root,flush=True)
