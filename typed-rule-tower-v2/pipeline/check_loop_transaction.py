"""Bounded transition equivalence checks and fail-closed evidence ledger.
This does not establish Rust refinement, runtime atomicity, or a Goggles theorem.
"""
import copy,json,sys,time,hashlib
from pathlib import Path
from shg_rule_tower import (Protocol,ROOT,seed,template,meta_construct,admit,apply_rule,
                           driver,source_pin,reserve_identity,expect_reject,digest,save,require)

def protected(p):
    return dict(phase=p.state,remaining=p.budget,pending=copy.deepcopy(p.pending),
                committed=sorted(p.committed),iteration=p.iteration,value=p.value)

def rank(s):
    return 0 if s['phase']=='terminated' else 2*s['remaining']+(1 if s['phase']=='ready' else 2)

def reference(s,event,key=None):
    """Independent declared finite-model transition, not native theorem authority."""
    out=copy.deepcopy(s)
    if event['kind']=='issue':
        require(s['phase']=='ready' and s['remaining']>0,'model-not-enabled')
        out.update(phase='waiting',remaining=s['remaining']-1,pending=key)
    elif event['kind']=='exhaust':
        require(s['phase']=='ready' and s['remaining']==0,'model-not-enabled')
        out['phase']='terminated'
    else:
        require(s['phase']=='waiting' and event['key']==s['pending'],'model-not-enabled')
        out['committed']=sorted(set(s['committed'])|{digest(event['key'])})
        out.update(pending=None,iteration=s['iteration']+1)
        if event['status']!='trap':out['value']=event['state']['word']
        out['phase']='ready' if event['status']=='continue' and s['remaining']>0 else 'terminated'
    return out

def finite_check(index):
    seen=set();cases=0;edges=[];terminal=False;success=False;rejection_cases=0
    # Exact finite domains. Identity tokens are one incarnation and monotone iterations.
    for budget in range(3):
        root=Protocol(index);root.budget=budget
        queue=[root]
        while queue:
            p=queue.pop();s=protected(p);signature=(budget,digest(s))
            if signature in seen:continue
            seen.add(signature)
            require((s['phase']=='waiting')==(s['pending'] is not None),'pending-invariant')
            require(0<=s['remaining']<=budget and s['iteration']<=budget,'budget-invariant')
            require(len(s['committed'])==s['iteration'],'commit-once-invariant')
            if s['phase']=='terminated':
                terminal=True;success|=s['value']==1;continue
            events=[{'kind':'issue'} if s['remaining'] else {'kind':'exhaust'}] if s['phase']=='ready' else [
                {'kind':'completion','key':copy.deepcopy(s['pending']),'status':status,'state':{'word':word}}
                for status in ['continue','halt','trap'] for word in [0,1]]
            for event in events:
                child=copy.deepcopy(p);key=child.transition(event);after=protected(child)
                require(after==reference(s,event,key),'model-interpreter-divergence')
                require(rank(after)<rank(s),'progress-rank')
                edges.append({'before':s,'event':event,'after':after});cases+=1;queue.append(child)
            if s['phase']=='waiting':
                for field in s['pending']:
                    bad=copy.deepcopy(s['pending']);bad[field]='other-incarnation' if field=='invocation' else bad[field]+1
                    q=copy.deepcopy(p)
                    expect_reject(lambda:q.transition({'kind':'completion','key':bad,'status':'continue','state':{'word':1}}),'correlation-mismatch')
                    require(protected(q)==s,'rejection-mutated-state');rejection_cases+=1
    require(terminal and success,'vacuous-model')
    return {'kind':'exhaustive-finite-transition-check','status':'passed','states':len(seen),'progress_edges':cases,
            'rejection_edges':rejection_cases,'domains':{'initial_budget':[0,1,2],'word':[0,1],'status':['continue','halt','trap'],
            'identities':'one fresh incarnation per initial model; monotonically allocated iterations'},
            'reachability':{'termination':terminal,'successful_commit':success},'transitions':edges,
            'silent_worker_counterexample':['Ready(1)','dispatch → Waiting(0)','idle → Waiting(0)','repeat forever'],
            'liveness':'not unconditional; matching completions and fair service required',
            'retry_profile':'unsupported; no timeout/cancellation/retry claim',
            'native_to_interpreter_general_proof':'open','runtime_atomicity':'open'}

def check_evidence_integrity(ledger,run,gate):
    """Receipt integrity/policy gate. It never promotes checks into theorems."""
    require(gate in ['bounded-model','behavioral','executable'],'unknown-gate')
    result=[]
    for obligation in ledger['obligations']:
        if gate not in obligation['gates']:continue
        require(obligation['subject']==ledger['subject'] and obligation['snapshot']==ledger['snapshot'],'obligation-scope')
        require(obligation['status']=='checked','obligation-open')
        path=run/obligation['evidence']['path']
        require(hashlib.sha256(path.read_bytes()).hexdigest()==obligation['evidence']['sha256'],'evidence-stale')
        if obligation['required_kind']=='checked-theorem':
            # Must consume a native admitted/rechecked theorem, never a JSON test banner.
            raise ValueError('native-theorem-required')
        require(obligation['evidence']['kind']==obligation['required_kind'],'evidence-kind')
        require(not obligation['dependencies'],'dependency-check-required')
        result.append(obligation['id'])
    require(result,'empty-gate')
    return {'gate':gate,'evidence_integrity_passed':True,'proof_closure':'not established','scope':'receipt integrity only; independent checker gate retained separately','obligations':result}

def main(run):
    run=Path(run);out=run/'formal-transaction';out.mkdir(exist_ok=True)
    index=json.loads((run/'grown/stage-1-index.json').read_text())
    checks=[]
    p=Protocol(index);q=Protocol(index);a=p.transition({'kind':'issue'});b=q.transition({'kind':'issue'})
    require(a!=b,'incarnation-reused');before=protected(q)
    checks.append(expect_reject(lambda:q.transition({'kind':'completion','key':a,'status':'continue','state':{'word':1}}),'correlation-mismatch'))
    require(protected(q)==before and q.budget==1,'nonresponding-worker-budget')
    checks.append(expect_reject(lambda:reserve_identity('execution',p.incarnation),'identity-already-reserved'))
    initial=seed();initial['placements'].append({**initial['placements'][0],'id':':second-run'})
    require(driver(out/'two-occurrences',[initial])==0,'two-occurrence-native')
    source=json.loads((out/'two-occurrences/stage-0-index.json').read_text())
    rule,_=meta_construct(template());admit(rule);params=dict(iteration_bound=2,effects=[':activate',':await',':publish',':terminate'],contract=':cycle-contract',correlation_type=':activation-key')
    subject=next(m['address'] for m in source['members'] if m['kind']=='occurrence' and m['semantic_id'][-1]=='second-run')
    pin=source_pin(initial,source);tx=reserve_identity('construction')
    candidate,env,trace,delta=apply_rule(rule,initial,source,params,subject,pin,tx)
    require(candidate['placements'][0]['child'] is None and candidate['placements'][1]['child'] is not None,'wrong-occurrence-target')
    require(driver(out/'second-selected',[initial,candidate])==0,'selected-successor-native')
    changed=copy.deepcopy(source);changed['graphs'][0]['header']['snapshot-ref']='changed-same-generation'
    checks.append(expect_reject(lambda:apply_rule(rule,initial,changed,params,subject,pin,tx),'source-pin-mismatch'))
    changed=copy.deepcopy(initial);changed['source_ref']=':different-source-same-generation'
    checks.append(expect_reject(lambda:apply_rule(rule,changed,source,params,subject,pin,tx),'source-pin-mismatch'))
    again,other,_,_=apply_rule(rule,initial,source,params,subject,pin,reserve_identity('construction'))
    require(env['controller']['value']!=other['controller']['value'],'allocation-namespace-reused')
    replay,replayed,_,_=apply_rule(rule,initial,source,params,subject,pin,tx)
    require(candidate==replay and env==replayed,'transaction-replay-nondeterministic')
    checks.append(expect_reject(lambda:apply_rule(rule,initial,source,{**params,'iteration_bound':1},subject,pin,tx),'transaction-binding-mismatch'))
    save(out/'review-counterexamples.json',{'status':'passed','checks':checks,'selected_subject':subject,'bindings':env,'delta':delta,
         'cross_instance_completion':'rejected','second_occurrence':'native grown, first remains open','dispatch_budget':'consumed while worker remains silent',
         'historical_namespace':'SQLite UNIQUE reservations, UUID namespace plus full SHA256 allocation; probabilistic UUID allocation, not a theorem of global uniqueness'})
    save(out/'finite-check.json',finite_check(index))
    machine=next(m for m in index['members'] if m['kind']=='machine')
    header=next(g['header'] for g in index['graphs'] if g['graph']==machine['graph'])
    ledger={'schema':'refinement-obligation-ledger-v1','subject':machine['address'],'snapshot':header['snapshot-ref'],'obligations':[
      {'id':'finite-model','subject':machine['address'],'snapshot':header['snapshot-ref'],'status':'checked','gates':['bounded-model'],
       'required_kind':'exhaustive-finite-transition-check','dependencies':[],
       'evidence':{'path':'finite-check.json','kind':'exhaustive-finite-transition-check','sha256':hashlib.sha256((out/'finite-check.json').read_bytes()).hexdigest()}},
      {'id':'implementation-correspondence','subject':machine['address'],'snapshot':header['snapshot-ref'],'status':'open','gates':['behavioral','executable'],
       'required_kind':'checked-theorem','dependencies':['finite-model'],'evidence':None}]}
    save(out/'obligations.json',ledger)
    model_result=check_evidence_integrity(ledger,out,'bounded-model');checks.append(expect_reject(lambda:check_evidence_integrity(ledger,out,'executable'),'obligation-open'))
    forged=copy.deepcopy(ledger);forged['obligations'][1].update(status='checked',evidence=forged['obligations'][0]['evidence'])
    checks.append(expect_reject(lambda:check_evidence_integrity(forged,out,'executable'),'native-theorem-required'))
    stale=copy.deepcopy(ledger);stale['obligations'][0]['evidence']['sha256']='0'*64
    checks.append(expect_reject(lambda:check_evidence_integrity(stale,out,'bounded-model'),'evidence-stale'))
    save(out/'closure.json',{'bounded_model_receipt':model_result,'behavioral':'open','liveness':'conditional, no general proof','executable':'blocked','negative_checks':checks})
    print('LOOP_TRANSACTION_GREEN',out)

if __name__=='__main__':main(sys.argv[1])
