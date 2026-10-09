"""Two independent proposals and paired targeted repairs per source; no semantic admission."""
import search as base
import json,time,copy,concurrent.futures,hashlib,urllib.request,importlib.util
from pathlib import Path
ROOT=Path(__file__).parent
SCHEMA=copy.deepcopy(base.SCHEMA)
cs=SCHEMA['properties']['candidates']['items']['properties']
cs['objects']['maxItems']=40;cs['relations']['maxItems']=48

def validate(c,occ):
 v=base.check(c,occ);lookup={t['id']:t['text'].lower() for t in occ};loss=[]
 for o in c['objects']:
  texts=[lookup.get(a,'') for a in o['anchors']]
  if o['kind']!='network' and (sum(t in ('was','were','is') for t in texts)>1 or sum(t in ('she','he','they','it') for t in texts)>1):
   loss.append('Occurrence correspondence requires review: '+o['id']+' merges distinct subjects/copulas; retain independent occurrences before grouping.')
 v['occurrence_diagnostics']=loss
 v['metrics']={'networks':sum(o['kind']=='network' for o in c['objects']),'network_operands':sum(e['target'] in {o['id'] for o in c['objects'] if o['kind']=='network'} for r in c['relations'] for e in r['ends']),'relation_operands':sum(e['target'] in {r['id'] for r in c['relations']} for r in c['relations'] for e in r['ends']),'implicit_positions':sum(o['kind'] in ('binder','position') for o in c['objects'])}
 return v

def propose(path,text,occ,seed,feedback=None):
 system='Generate one source-grounded semantic graph hypothesis, not a summary. No operator inventory or intended topology is supplied. Preserve independently occurring subjects and predicates as separately addressable occurrences. Groupings must retain those identities in networks. At most 40 objects and 48 relations; use only as many as justified. Objects n0,n1,... and relations r0,r1,...; anchors are source token IDs. Only networks have members. All members and endpoints must exist; no self-containment. Missing grammatical positions require a named construction license and explicit position/binder objects when that analysis needs them. Argument, binding, scope, attachment and inference are distinct. A network or relation may itself be an operand, but never fabricate a higher-order relation merely to satisfy a metric. Every license is a proposed meaning, not native authority. Preserve unresolved readings. Feedback: repair only diagnosed problems supported by the source; do not treat model judgments as proof.'
 state={'source':text,'occurrences':occ,'sampling_seed':seed,'feedback':feedback,'semantic_admission':'unavailable: grammatical/operator laws need native validation'}
 body={'model':'local','messages':[{'role':'system','content':system},{'role':'user','content':json.dumps(state,separators=(',',':'))}],'temperature':0.55,'seed':seed,'max_tokens':6500,'chat_template_kwargs':{'enable_thinking':False},'response_format':{'type':'json_schema','json_schema':{'name':'graph_hypothesis','strict':True,'schema':SCHEMA}}}
 base.save(path/'request.json',body);start=time.monotonic()
 try:
  resp=base.post('http://127.0.0.1:8088/v1/chat/completions',body);base.save(path/'response.json',resp)
  if resp['choices'][0]['finish_reason']!='stop':raise ValueError('incomplete generation retained')
  result={'status':'COMPLETED','proposal':json.loads(resp['choices'][0]['message']['content'])}
 except Exception as e:result={'status':'FAILED','error':str(e)}
 result['seconds']=round(time.monotonic()-start,2);base.save(path/'result.json',result);return result

def observers(path,text,c):
 # One exact relation and its endpoint descriptions; no full-graph Laya request.
 rel=c['relations'][0] if c['relations'] else None
 objs={o['id']:o for o in c['objects']}
 local={'source':text,'relation':rel,'operands':[{'id':e['target'],'type':objs.get(e['target'],{}).get('type'),'anchors':objs.get(e['target'],{}).get('anchors')} for e in rel['ends']] if rel else []}
 q={'fit':{'type':'choice','instructions':'Is this exact proposed relation licensed by the source?','criteria':{'supported':'Source supports roles.','unsupported':'Roles conflict with source.','unresolved':'Insufficient evidence.'}}}
 # Compact source still retained in full; truncate nothing. If service drops tokens reject.
 body={'model':'english','state':local,'questions':q};base.save(path/'laya-request.json',body)
 try:
  resp=base.post('http://127.0.0.1:8091/v1/systemone',body);base.save(path/'laya-response.json',resp)
  l={'status':'REJECTED_TRUNCATED' if resp.get('usage',{}).get('truncated') or resp.get('usage',{}).get('state_tokens_dropped') else 'COMPLETED','answers':resp.get('answers',{})}
 except Exception as e:l={'status':'FAILED','error':str(e)}
 base.save(path/'laya.json',l)
 return l

def case(root,name,text,origin):
 p=root/name;occ=base.tokens(text);base.save(p/'source.json',{'text':text,'origin':origin,'sha256':base.sha(text.encode())});base.save(p/'occurrences.json',occ)
 candidates=[];pairs=[]
 for seed in (17,29):
  a=propose(p/str(seed)/'initial',text,occ,seed)
  if a['status']!='COMPLETED':pairs.append({'seed':seed,'initial':a['status']});continue
  c=a['proposal']['candidates'][0];c['id']=f'initial-{seed}';check=validate(c,occ);candidates.append(c)
  obs=observers(p/str(seed)/'observers',text,c)
  feedback={'candidate':c,'errors':check['errors'],'occurrence_diagnostics':check['occurrence_diagnostics'],'backward_goals':check['backward_goals'][:4],'laya':obs}
  b=propose(p/str(seed)/'feedback',text,occ,seed,feedback)
  pair={'seed':seed,'initial':check,'feedback_generation':b['status'],'laya':obs}
  if b['status']=='COMPLETED':
   d=b['proposal']['candidates'][0];d['id']=f'feedback-{seed}';candidates.append(d);pair['feedback']=validate(d,occ)
  pairs.append(pair);base.save(p/'pairs.json',pairs)
  print(json.dumps({'source':name,'seed':seed,'feedback':b['status'],'candidate_count':len(candidates)}),flush=True)
 checks={c['id']:validate(c,occ) for c in candidates};base.save(p/'candidates.json',candidates);base.save(p/'checks.json',checks)
 # Jev compares all complete actual candidate graphs, independent of native admission.
 if candidates:
  try:
   spec=importlib.util.spec_from_file_location('jev',Path('/home/user0/research-gold-disrpt/corpusGraph/scripts/jev_systemone.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
   state={'source':text,'candidates':candidates};question={'fit':{'type':'choice','instructions':'Compare exact graph hypotheses against unchanged source. Select best source support, or unresolved. Scores do not prove meaning.','criteria':{**{c['id']:c['reading'] for c in candidates},'unresolved':'No justified selection.'}}}
   base.save(p/'jev-request.json',{'state':state,'questions':question});base.save(p/'jev-response.json',m.decide(json.dumps(state),question))
  except Exception as e:base.save(p/'jev-error.json',{'error':str(e)})
 return {'source':name,'candidates':len(candidates),'pairs':pairs,'semantic_admission':'NOT_RUN'}

if __name__=='__main__':
 root=ROOT/'expanded-runs'/str(time.time_ns());root.mkdir(parents=True,mode=0o700)
 base.save(root/'pins.json',{str(p):base.sha(p.read_bytes()) for p in [Path(__file__),Path(base.__file__)]})
 print(str(root),flush=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  futures=[pool.submit(case,root,*s) for s in base.sources()];reports=[f.result() for f in futures]
 base.save(root/'results.json',reports);base.atomic_text(ROOT/'expanded-latest.txt',str(root)+'\n')
 base.save(root/'manifest.json',{str(p.relative_to(root)):base.sha(p.read_bytes()) for p in root.rglob('*') if p.is_file()})
 print('DONE '+str(root),flush=True)
