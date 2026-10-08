"""Typed template -> admitted construction rule -> native SHG -> bounded protocol trace."""
import copy,hashlib,json,subprocess,time
from pathlib import Path
from vm_add_tower import ROOT,ROUTER,lisp
NATIVE=ROOT.parent/'ORCHESTRATION/worktrees/goggles-vm-feedback-47fe6800'
EFFECTS=[':activate',':await',':publish',':terminate']
CONTRACT=':cycle-contract'

def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def require(test,category):
    if not test:raise ValueError(category)

def seed():
    types=[dict(id=':vm-state',schema=[':record',':word',':u32'],refinements=[]),dict(id=':run-outcome',schema=[':result',':vm-state',':halt-trap-budget'],refinements=[]),dict(id=':activation-key',schema=[':record',':graph-generation',':natural',':input-generation',':natural',':invocation',':string',':iteration',':natural',':attempt',':natural'],refinements=[]),dict(id=':activation-request',schema=[':record',':key',':activation-key',':state',':vm-state'],refinements=[]),dict(id=':step-completion',schema=[':record',':key',':activation-key',':state',':vm-state',':status',':continue-halt-trap'],refinements=[]),dict(id=':controller-state',schema=[':record',':budget',':natural',':carried-state',':vm-state',':pending-key',':activation-key'],refinements=[])]
    for guard in [':positive-budget',':continue',':stop',':halt',':trap']:
        types.append(dict(id=guard,schema=[':predicate',[':controller-state'] if guard==':positive-budget' else [':controller-state',':step-completion'],':boolean',guard],refinements=[]))
    effects=[dict(id=name,input=inp,output=out,constraints=[]) for name,inp,out in [(':activate',':vm-state',':activation-request'),(':await',':step-completion',':step-completion'),(':publish',':step-completion',':vm-state'),(':terminate',':step-completion',':run-outcome')]]
    ports=[dict(id=':run-state',direction=':in',value_type=':vm-state',effects=EFFECTS,contract=CONTRACT),dict(id=':run-outcome-port',direction=':out',value_type=':run-outcome',effects=EFFECTS,contract=CONTRACT)]
    return dict(schema=':shg-declarations-v1',id=':vm-feedback',generation=0,source_ref=':typed-rule-tower-v1',limits=dict(max_depth=4,max_occurrences=12,max_relations=1024,max_input_nodes=4096),types=types,effects=effects,contracts=[dict(id=CONTRACT,assume=[':environment-may-not-complete'],guarantee=[':matching-completion-only',':trap-preserves-carried-state'],invariants=[':one-pending-request'],effects=EFFECTS,dependencies=[])],port_definitions=ports,node_types=[dict(id=':run-node',ports=[':run-state',':run-outcome-port'],operations=[':run'],machine=':unbound',contract=CONTRACT)],machines=[],operations=[dict(id=':run',inputs=[':run-state'],outputs=[':run-outcome-port'],preconditions=[],postconditions=[':bounded-step-loop'],effects=EFFECTS,contract=CONTRACT)],memory=[],bindings=[],placements=[dict(id=':run',type=':run-node',parent=':none',state=':unbound',memory=':unbound',provider=':unbound',child=None)],connections=[],children=[])

# Checked template data: all variable uses are explicitly declared; no inference from nesting.
FRESH={name:{'type':typ,'scope':'$root_graph' if name=='cycle_graph' else '$cycle_graph'} for name,typ in [
 ('cycle_graph','GraphId'),('controller','PlacementId'),('worker','PlacementId'),('machine','MachineId'),('call','RelationIntentId'),('cycle','RelationIntentId'),('controller_op','OperationId'),('worker_op','OperationId'),('controller_node','NodeTypeId'),('worker_node','NodeTypeId'),('seed_port','PortId'),('outcome_port','PortId'),('request_port','PortId'),('receive_port','PortId'),('argument_port','PortId'),('result_port','PortId')]}

def template():
    ports=[('$seed_port',':in',':vm-state'),('$outcome_port',':out',':run-outcome'),('$request_port',':out',':activation-request'),('$receive_port',':in',':step-completion'),('$argument_port',':in',':activation-request'),('$result_port',':out',':step-completion')]
    objects=[]
    for name,direction,typ in ports:objects.append(('port_definitions',dict(id=name,direction=direction,value_type=typ,effects='$effects',contract='$contract')))
    for op,ins,outs,post in [('$controller_op',['$seed_port','$receive_port'],['$outcome_port','$request_port'],[':bounded-step-loop']),('$worker_op',['$argument_port'],['$result_port'],[':abstract-step-callee'])]:
        objects.append(('operations',dict(id=op,inputs=ins,outputs=outs,preconditions=[],postconditions=post,effects='$effects',contract='$contract')))
    transitions=[]
    for ident,start,end,guard,trigger,effects in [('issue',':ready',':waiting',':positive-budget',':activation-request',[':activate',':await']),('continue',':waiting',':ready',':continue',':step-completion',[':publish']),('budget',':waiting',':terminated',':stop',':step-completion',[':publish',':terminate']),('halt',':waiting',':terminated',':halt',':step-completion',[':publish',':terminate']),('trap',':waiting',':terminated',':trap',':step-completion',[':terminate'])]:
        transitions.append(dict(id=':'+ident,from_=start,to=end,trigger=trigger,guard=guard,operation='$controller_op',effects=effects,contract='$contract'))
    # Lisp serializer maps trailing '_' too; canonical key must be 'from'.
    for t in transitions:t['from']=t.pop('from_')
    objects.append(('machines',dict(id='$machine',states=[':ready',':waiting',':terminated'],initial=':ready',transitions=transitions)))
    objects.extend([('node_types',dict(id='$controller_node',ports=['$seed_port','$outcome_port','$request_port','$receive_port'],operations=['$controller_op'],machine='$machine',contract='$contract')),('node_types',dict(id='$worker_node',ports=['$argument_port','$result_port'],operations=['$worker_op'],machine=':unbound',contract='$contract'))])
    for name,node,state in [('$controller','$controller_node',':ready'),('$worker','$worker_node',':unbound')]:objects.append(('placements',dict(id=name,type=node,parent=':none',state=state,memory=':unbound',provider=':unbound',child=None)))
    pairs=[('$controller','$request_port'),('$worker','$argument_port'),('$worker','$result_port'),('$controller','$receive_port')]
    objects.append(('connections',dict(id='$call',type=':call',ends=[dict(role=role,placement=p,port=q) for role,(p,q) in zip([':caller',':argument',':result',':return'],pairs)],contract='$contract',effects='$effects',handler=':unbound',callee_operation='$worker_op')))
    objects.append(('connections',dict(id='$cycle',type=':activation-feedback',ends=[dict(role=role,placement=p,port=q) for role,(p,q) in zip([':controller',':activation',':completion',':continuation'],pairs)],contract='$contract',effects='$effects',handler=':unbound',machine='$machine',correlation_schema='$correlation_type',iteration_bound='$iteration_bound',work_relation=[':relation','$cycle_graph','$call'])))
    program=[dict(op='nest',body='$body_address',graph='$cycle_graph')]
    program += [dict(op='append',graph='$cycle_graph',collection=c,value=v) for c,v in objects]
    program.append(dict(op='enclose',graph='$cycle_graph',map=[dict(outer=':run-state',inner_placement='$controller',inner_port='$seed_port'),dict(outer=':run-outcome-port',inner_placement='$controller',inner_port='$outcome_port')]))
    signature={'body_address':'NativeAddress','root_graph':'GraphId','iteration_bound':'PositiveBound','effects':'EffectSet','contract':'ContractId','correlation_type':'TypeId'}
    interface={'ports':[dict(name=n,direction='in',value_type=t) for n,t in signature.items()]+[dict(name='delta',direction='out',value_type='GraphDelta'),dict(name='obligations',direction='out',value_type='ObligationSet')], 'boundary_map':[dict(outer=n,inner='produce.'+n) for n in list(signature)+['delta','obligations']]}
    return dict(schema='coordination-rule-v1',id='grow-vm-iteration-v1',match={'kind':'occurrence','node_type':':run-node','body':'open','bind':{'body_address':'NativeAddress','root_graph':'GraphId'}},parameters={'iteration_bound':'PositiveBound','effects':'EffectSet','contract':'ContractId','correlation_type':'TypeId'},fresh=FRESH,requires=['current-native-subject','body-open','allowed-effects','finite-growth'],produce={'type':'ConstructionProgram','inputs':signature,'outputs':{'delta':'GraphDelta','obligations':'ObligationSet'},'instructions':program},obligations=['boundary-preservation','effect-containment','matching-completion','environmental-liveness-unproven','behavioral-refinement-unproven'],interface=interface)

ACTIVE={}
def meta_construct(source):
    # Same structural basis: append complete fields, nest production, enclose typed interface.
    result={};trace=[]
    for k in ['schema','id','match','parameters','fresh','requires','obligations']:
        result[k]=copy.deepcopy(source[k]);trace.append({'op':'append','field':k,'value_digest':digest(source[k])})
    result['produce']=copy.deepcopy(source['produce']);trace.append({'op':'nest','field':'produce','value_digest':digest(source['produce'])})
    result['interface']=copy.deepcopy(source['interface']);trace.append({'op':'enclose','boundary_map':source['interface']['boundary_map'],'meaning':'map typed outer rule ports onto production-program ports; parameter substitution is separate'})
    result['identity']=digest(result)
    return result,trace

def variables(x):
    if isinstance(x,str):return {x[1:]} if x.startswith('$') else set()
    if isinstance(x,list):return set().union(*(variables(v) for v in x)) if x else set()
    if isinstance(x,dict):return set().union(*(variables(v) for v in x.values())) if x else set()
    return set()

def admit(rule):
    require(set(rule)=={'schema','id','match','parameters','fresh','requires','produce','obligations','interface','identity'},'rule-schema')
    require(digest({k:v for k,v in rule.items() if k!='identity'})==rule['identity'],'rule-identity')
    require(rule['schema']=='coordination-rule-v1' and rule['produce']['type']=='ConstructionProgram','production-type')
    inputs=rule['produce']['inputs'];outputs=rule['produce']['outputs']
    ports=rule['interface']['ports'];maps=rule['interface']['boundary_map']
    require(len(ports)==len(inputs)+len(outputs) and len(maps)==len(ports),'rule-boundary-totality')
    for port,mapping in zip(ports,maps):
        inner=inputs if port['direction']=='in' else outputs
        require(inner.get(port['name'])==port['value_type'] and mapping=={'outer':port['name'],'inner':'produce.'+port['name']},'rule-boundary-type')
    require(inputs=={**rule['match']['bind'],**rule['parameters']},'rule-parameter-correspondence')
    bound=set(rule['match']['bind']);params=set(rule['parameters']);fresh=set(rule['fresh'])
    require(not(bound&params or bound&fresh or params&fresh),'binding-class-collision')
    require(variables(rule)<=bound|params|fresh,'unbound-rule-variable')
    require(rule['requires']==['current-native-subject','body-open','allowed-effects','finite-growth'],'unknown-precondition')
    require(set(rule['obligations'])==set(template()['obligations']),'missing-obligation')
    # Bounded admission: exact checked template semantics, not arbitrary rule inference.
    canonical,_=meta_construct(template());require(rule==canonical,'unsupported-construction-semantics')
    ACTIVE[rule['identity']]=copy.deepcopy(rule)
    return {'status':'structurally-admitted-to-bounded-registry','rule':rule['identity'],'behavioral_proof':'open','scope':'exact checked coordination template'}

def apply_rule(rule,initial,index,params):
    require(rule['identity'] in ACTIVE and ACTIVE[rule['identity']]==rule,'rule-not-admitted')
    require(set(params)==set(rule['parameters']),'parameter-binding')
    require(type(params['iteration_bound']) is int and 0<params['iteration_bound']<=4096,'iteration-bound')
    require(params['effects']==EFFECTS and params['contract']==CONTRACT and params['correlation_type']==':activation-key','profile-binding')
    subject=next(m for m in index['members'] if m['kind']=='occurrence' and m['fields']['type']=='run-node')
    require(isinstance(subject['fields']['body'],list) and subject['fields']['body'][0]=='hole','body-not-open')
    require(index['graphs'][0]['generation']==initial['generation'],'stale-subject')
    env={'body_address':{'class':'matched','type':'NativeAddress','value':subject['address'],'scope':initial['id']},'root_graph':{'class':'matched','type':'GraphId','value':initial['id'],'scope':initial['id']}}
    for name,typ in rule['parameters'].items():env[name]={'class':'parameter','type':typ,'value':copy.deepcopy(params[name]),'scope':initial['id']}
    for name,spec in rule['fresh'].items():
        value=':'+name.replace('_','-')+'-'+digest([rule['identity'],subject['address'],name])[:8]
        env[name]={'class':'fresh','type':spec['type'],'value':value,'scope':spec['scope']}
    for name in rule['fresh']:
        scope=env[name]['scope'];env[name]['scope']=env[scope[1:]]['value']
    require(len({e['value'] for e in env.values() if e['class']=='fresh'})==len(rule['fresh']),'fresh-allocation-collision')
    def resolve(x):
        if isinstance(x,str) and x.startswith('$'):return copy.deepcopy(env[x[1:]]['value'])
        if isinstance(x,list):return [resolve(v) for v in x]
        if isinstance(x,dict):return {k:resolve(v) for k,v in x.items()}
        return x
    candidate=copy.deepcopy(initial);candidate['generation']+=1
    candidate['source_ref']=[':construction-rule',rule['identity'],':parent-address',subject['address'],':bindings',digest(env)]
    child=None;trace=[]
    for statement in rule['produce']['instructions']:
        op=resolve(statement)
        if op['op']=='nest':
            require(op['body']==subject['address'] and child is None,'nest-target')
            child={k:copy.deepcopy(v) for k,v in candidate.items()};child['id']=op['graph'];child['placements']=[];child['port_definitions']=[];child['node_types']=[];child['operations']=[];child['machines']=[];child['connections']=[];child['children']=[]
        elif op['op']=='append':
            require(child is not None and op['graph']==child['id'],'append-scope')
            require(op['collection'] in ['port_definitions','operations','node_types','machines','placements','connections'],'append-collection')
            require(not any(x['id']==op['value']['id'] for x in child[op['collection']]),'duplicate-append')
            child[op['collection']].append(op['value'])
        elif op['op']=='enclose':
            require(child is not None and op['graph']==child['id'],'enclose-scope')
            require({m['outer'] for m in op['map']}=={':run-state',':run-outcome-port'},'boundary-totality')
            candidate['placements'][0]['child']=child['id'];candidate['children']=[dict(id=child['id'],declaration=child,boundary_map=op['map'])]
        else:raise ValueError('unknown-primitive')
        trace.append({'statement':op,'status':'staged','publication':'not-yet-native-validated'})
    require(candidate['children'] and len(child['connections'])==2,'incomplete-production')
    return candidate,env,trace,{'parent_address':subject['address'],'parent_generation':initial['generation'],'rule_identity':rule['identity'],'added_child':child,'boundary_map':candidate['children'][0]['boundary_map'],'obligations':rule['obligations'],'admission':'candidate-pending-native-checks'}


def driver(run,stages):
    # Reuse the existing immutable-check driver; fix its JSON array/plist discrimination locally.
    source=(ROOT/'synthesis/vm_add_tower.lisp').read_text().replace('/home/user0/ORCHESTRATION/worktrees/literate-goggles-pr192-33d30ba0/',str(NATIVE)+'/')
    fields=['stages','address_ref_ascii','source_bundle_snapshot_ref','occurrence_scope_ref','source_registry_root_ref','source_registry_kind_ascii','source_row_ref_ascii','source_row_digest_32b_hex','h002_resolution_receipt_ref','boundary_contract_ref','object_class_ref_ascii','graph','generation','identity','header','history','semantic_id','kind','address','fields','graphs','members','dataflows','id','ends','contract','stage','addresses','replay','stale_address_rejected','semantic_admission','schema','version','root','bundle-ref','snapshot-ref','registries-ref','lifecycle','owner','definition','direction','value-type','effects','type','parent','state','memory','provider','body','role','occurrence','port','ordinal','input','output','constraints','assume','guarantee','invariants','dependencies','machine','ports','operations','states','initial','transitions','from','to','trigger','guard','operation','boundary','inputs','outputs','preconditions','postconditions','claim','status','subject','method','evidence','source-ref','ontology-ref','reason','correlation-schema','iteration-bound','work-relation','callee-operation','native-root-address','open_region','path','member']
    test="(and (listp value)(evenp(length value))(loop for (k v) on value by #'cddr always(keywordp k)))"
    source=source.replace(test,"(and (listp value)(evenp(length value))(member(first value)'("+' '.join(':'+k for k in fields)+"))(loop for (k v) on value by #'cddr always(keywordp k)))")
    run.mkdir(parents=True,exist_ok=True);(run/'driver.lisp').write_text(source);(run/'declarations.sexp').write_text(lisp(stages)+'\n')
    with (run/'native.log').open('w') as out:return subprocess.run(['sbcl','--script',str(run/'driver.lisp'),str(run/'declarations.sexp'),str(run)],stdout=out,stderr=subprocess.STDOUT,timeout=180).returncode

class Protocol:
    """Bounded interpreter of the actual native machine table; no provider execution."""
    def __init__(self,index):
        self.relation=next(m for m in index['members'] if m['kind']=='relation' and m['fields']['type']=='activation-feedback')
        g=self.relation['graph'];ident=self.relation['fields']['machine']
        self.machine=next(m for m in index['members'] if m['graph']==g and m['kind']=='machine' and m['semantic_id']==ident)
        self.state=self.machine['fields']['initial'];self.budget=self.relation['fields']['iteration-bound'];self.iteration=0;self.value=0;self.pending=None;self.trace=[]
        self.generation=next(x['generation'] for x in index['graphs'] if x['graph']==g)
    def transition(self,event):
        require(event.get('kind') in ['issue','completion'],'event-kind')
        require(set(event)==({'kind'} if event['kind']=='issue' else {'kind','key','status','state'}),'event-fields')
        # Verify all completion identity and payload constraints before changing state.
        if event['kind']=='completion':
            require(self.state=='waiting' and self.pending is not None,'no-pending-activation')
            require(isinstance(event['key'],dict) and set(event['key'])==set(self.pending),'correlation-schema')
            require(type(event['key']['invocation']) is str and all(type(event['key'][k]) is int and event['key'][k]>=0 for k in ['graph_generation','input_generation','iteration','attempt']),'correlation-type')
            require(event['key']==self.pending,'correlation-mismatch')
            require(event['status'] in ['continue','halt','trap'],'completion-status')
            require(isinstance(event['state'],dict) and set(event['state'])=={'word'} and type(event['state']['word']) is int and 0<=event['state']['word']<2**32,'completion-state-type')
        def predicate(name):
            return {'positive-budget':self.budget>0,'continue':event.get('status')=='continue' and self.budget>1,'stop':event.get('status')=='continue' and self.budget==1,'halt':event.get('status')=='halt','trap':event.get('status')=='trap'}[name]
        trigger='activation-request' if event['kind']=='issue' else 'step-completion'
        ts=[t for t in self.machine['fields']['transitions'] if t['from']==self.state and t['trigger']==trigger and predicate(t['guard'])]
        require(len(ts)==1,'transition-readiness')
        t=ts[0];before={'state':self.state,'budget':self.budget,'iteration':self.iteration,'value':self.value}
        if event['kind']=='issue':
            self.pending=dict(graph_generation=self.generation,input_generation=0,invocation='demo',iteration=self.iteration,attempt=0)
        else:
            if 'publish' in t['effects']:self.value=event['state']['word']
            self.budget-=1;self.iteration+=1;self.pending=None
        self.state=t['to'];self.trace.append({'machine_address':self.machine['address'],'hyperedge_address':self.relation['address'],'event':copy.deepcopy(event),'transition':t,'before':before,'after':{'state':self.state,'budget':self.budget,'iteration':self.iteration,'value':self.value},'pending':copy.deepcopy(self.pending),'emitted_request':{'key':copy.deepcopy(self.pending),'state':{'word':self.value}} if event['kind']=='issue' else None})
        return copy.deepcopy(self.pending)

def expect_reject(fn,category):
    try:fn()
    except ValueError as e:require(str(e)==category,'wrong-rejection:'+str(e));return {'expected':category,'rejected':True}
    raise AssertionError('Accepted '+category)

def main():
    run=ROOT/'runs/typed-rule-tower'/str(time.time_ns());run.mkdir(parents=True);print('Run:',run,flush=True)
    initial=seed();require(driver(run/'seed',[initial])==0,'native-seed')
    index=json.loads((run/'seed/stage-0-index.json').read_text())
    checked=template();save(run/'checked-template.json',checked)
    rule,meta=meta_construct(checked);save(run/'generated-rule.json',rule);save(run/'meta-construction-trace.json',meta)
    receipt=admit(rule);save(run/'rule-admission.json',receipt)
    params=dict(iteration_bound=2,effects=EFFECTS,contract=CONTRACT,correlation_type=':activation-key')
    candidate,env,trace,delta=apply_rule(rule,initial,index,params)
    save(run/'binding-environment.json',env);save(run/'interpreter-trace.json',trace);save(run/'graph-delta.json',delta)
    require(driver(run/'grown',[initial,candidate])==0,'native-grown')
    final=json.loads((run/'grown/stage-1-index.json').read_text())
    nativechecks=json.loads((run/'grown/native-checks.json').read_text())
    save(run/'graph-admission.json',{'status':'structurally-validated-candidate','native_replay':nativechecks['replay'],'boundary_effect_checks':True,'behavioral_proof':'open','liveness':'unproven-environment-dependent','executable_admission':False})
    protocol=Protocol(final)
    for i in range(2):
        key=protocol.transition({'kind':'issue'});protocol.transition({'kind':'completion','key':key,'status':'continue','state':{'word':i+1}})
    require(protocol.state=='terminated' and protocol.value==2,'feedback-trace')
    save(run/'runtime-transition-trace.json',protocol.trace)
    negatives=[]
    broken=copy.deepcopy(rule);broken['parameters'].pop('iteration_bound');broken['identity']=digest({k:v for k,v in broken.items() if k!='identity'});negatives.append(expect_reject(lambda:admit(broken),'rule-parameter-correspondence'))
    broken=copy.deepcopy(rule);broken['obligations']=[];broken['identity']=digest({k:v for k,v in broken.items() if k!='identity'});negatives.append(expect_reject(lambda:admit(broken),'missing-obligation'))
    broken=copy.deepcopy(rule);broken['fresh']['controller']['scope']='$undeclared_scope';broken['identity']=digest({k:v for k,v in broken.items() if k!='identity'});negatives.append(expect_reject(lambda:admit(broken),'unbound-rule-variable'))
    broken=copy.deepcopy(rule);broken['interface']['boundary_map'][0]['inner']='produce.effects';broken['identity']=digest({k:v for k,v in broken.items() if k!='identity'});negatives.append(expect_reject(lambda:admit(broken),'rule-boundary-type'))
    negatives.append(expect_reject(lambda:apply_rule(rule,initial,index,{**params,'iteration_bound':0}),'iteration-bound'))
    p=Protocol(final);negatives.append(expect_reject(lambda:p.transition({'kind':'invented'}),'event-kind'))
    key=p.transition({'kind':'issue'});bad=copy.deepcopy(key);bad['graph_generation']=True
    negatives.append(expect_reject(lambda:p.transition({'kind':'completion','key':bad,'status':'continue','state':{'word':1}}),'correlation-type'))
    for state in [{'word':True},{'word':2**32},{'other':1}]:
        p=Protocol(final);key=p.transition({'kind':'issue'});before=copy.deepcopy(p.__dict__)
        negatives.append(expect_reject(lambda:p.transition({'kind':'completion','key':key,'status':'continue','state':state}),'completion-state-type'));require(p.__dict__==before,'rejection-mutated-state')
    for field in ['graph_generation','input_generation','invocation','iteration','attempt']:
        p=Protocol(final);key=p.transition({'kind':'issue'});bad=copy.deepcopy(key);bad[field]='other' if field=='invocation' else key[field]+1
        before=copy.deepcopy(p.__dict__);negatives.append(expect_reject(lambda:p.transition({'kind':'completion','key':bad,'status':'continue','state':{'word':1}}),'correlation-mismatch'));require(p.__dict__==before,'rejection-mutated-state')
    p=Protocol(final);key=p.transition({'kind':'issue'});p.transition({'kind':'completion','key':key,'status':'continue','state':{'word':1}});negatives.append(expect_reject(lambda:p.transition({'kind':'completion','key':key,'status':'continue','state':{'word':1}}),'no-pending-activation'))
    for status in ['halt','trap']:
        p=Protocol(final);key=p.transition({'kind':'issue'});p.transition({'kind':'completion','key':key,'status':status,'state':{'word':7}});require(p.state=='terminated' and p.value==(0 if status=='trap' else 7),'exit-semantics')
    # Native malformed coordination candidates; each rejection must name its actual reason.
    for name,mutate,reason in [
        ('missing-role',lambda c:c['connections'][1]['ends'].pop(),'SHG feedback requires exactly four distinct roles'),
        ('wrong-request-type',lambda c:c['port_definitions'][4].update(value_type=':step-completion'),'SHG call typed argument/result or ownership mismatch'),
        ('undeclared-effect',lambda c:c['connections'][1].update(effects=[':unknown-effect']),'SHG required reference does not resolve'),
        ('missing-transition',lambda c:c['machines'][0]['transitions'].pop(),'SHG feedback transition profile invalid'),
        ('wrong-guard-type',lambda c:c['types'][-1].update(schema=':integer'),'SHG feedback guard signature invalid'),
        ('missing-boundary',lambda c:None,'SHG child boundary is not total')]:
        bad=copy.deepcopy(candidate);c=bad['children'][0]['declaration'];mutate(c)
        if name=='missing-boundary':bad['children'][0]['boundary_map'].pop()
        path=run/'negative-native'/name;status=driver(path,[initial,bad]);log=(path/'native.log').read_text()
        require(status!=0 and reason in log,'wrong-native-rejection:'+name);negatives.append({'case':name,'expected':reason,'rejected':True})
    save(run/'negative-checks.json',negatives)
    metadata=json.loads(subprocess.check_output(['cargo','metadata','--format-version','1','--no-deps','--manifest-path',str(ROUTER/'Cargo.toml')],text=True));binary=Path(metadata['target_directory'])/'debug/examples/h002_file_lookup';receipts=[]
    for row in json.loads((run/'grown/stage-1-exports.json').read_text()):
        p=run/'lookup.json';save(p,[row]);r=json.loads(subprocess.check_output([str(binary),str(p)],text=True));require(r['selected_address_ref']==row['address_ref_ascii'] and not r['executable_realization_admitted'],'r001-lookup');receipts.append(r)
    save(run/'router-receipts.json',receipts)
    patch=subprocess.check_output(['git','-C',str(NATIVE),'diff'],text=True)+(NATIVE/'lisp/shg_activation_feedback_v1.lisp').read_text();(run/'native-changes.txt').write_text(patch)
    result={'rule_identity':rule['identity'],'seed_addresses':len(index['members']),'grown_addresses':len(final['members']),'negative_checks':len(negatives),'r001_selected':len(receipts),'feedback_trace':'two correlated successes then budget termination','halt_trap_checked':True,'native_source':str(NATIVE),'base_commit':subprocess.check_output(['git','-C',str(NATIVE),'rev-parse','HEAD'],text=True).strip(),'native_files_sha256':{str(p.relative_to(NATIVE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [NATIVE/'lisp/shg_encapsulator_v1.lisp',NATIVE/'lisp/shg_activation_feedback_v1.lisp',NATIVE/'lsip-shg-encapsulator-v1.asd']},'structural_admission_only':True,'behavioral_liveness_proof':'open','dispatch':'bounded protocol interpreter; no provider or VM instruction execution','interpreter_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    save(run/'result.json',result)
    root=next(g for g in final['graphs'] if g['graph']=='vm-feedback')
    publication={'status':'structurally-validated-only','graph':str(run/'grown/stage-1.sexp'),'graph_sha256':hashlib.sha256((run/'grown/stage-1.sexp').read_bytes()).hexdigest(),'root_header':root['header'],'rule_identity':rule['identity'],'parent_subject':env['body_address']['value']}
    save(run/'accepted-graph.pending.json',publication);(run/'accepted-graph.pending.json').replace(run/'accepted-graph.json')
    print('TYPED_RULE_TOWER_GREEN',run,flush=True);print(json.dumps(result,indent=2))

if __name__=='__main__':main()
