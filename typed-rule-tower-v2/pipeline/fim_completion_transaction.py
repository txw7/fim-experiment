"""Actual local raw FIM candidate; exact binding and tests, no proof promotion."""
import copy,hashlib,json,subprocess,sys,urllib.request
from pathlib import Path
from shg_rule_tower import ROOT,save,require
from serialize_fim import serialize
from apply_candidate import apply
PREFIX='''// Pure completion acceptance, proposed leaf realization under the addressed controller operation.
// Return None for non-Waiting state, absent pending, wrong full key, already committed key,
// or invalid status (status 0=continue, 1=halt, 2=trap). No input mutation.
// Accept: clone state, clear pending, append key exactly once; budget already consumed at dispatch.
// Continue iff status==0 and remaining>0. Otherwise terminate. Trap preserves word.
#[derive(Clone, Debug, PartialEq, Eq)]
struct Key { generation:u64, input_generation:u64, incarnation:String, iteration:u64, attempt:u64 }
#[derive(Clone, Debug, PartialEq, Eq)]
struct State { phase:u8, remaining:u32, pending:Option<Key>, committed:Vec<Key>, word:u32 }
#[derive(Clone)]
struct Completion { key:Key, status:u8, word:u32 }
// phase 0=Ready, 1=Waiting, 2=Terminal. Generate only this function body.
fn accept_completion(state:&State, completion:&Completion)->Option<State> {
'''
SUFFIX='''
}
#[cfg(test)] mod tests {
use super::*;
fn fixture()->(State,Completion) {
 let k=Key{generation:1,input_generation:0,incarnation:"incarnation-a".into(),iteration:0,attempt:0};
 (State{phase:1,remaining:1,pending:Some(k.clone()),committed:vec![],word:7},Completion{key:k,status:0,word:9})
}
#[test] fn valid_and_budget() { for budget in 0..=2 {for status in 0..=2 {let (mut s,mut c)=fixture();s.remaining=budget;c.status=status;let a=accept_completion(&s,&c).unwrap();assert_eq!(s.word,7);assert_eq!(a.remaining,budget);assert_eq!(a.pending,None);assert_eq!(a.committed,vec![c.key]);assert_eq!(a.phase,if status==0 && budget>0 {0}else{2});assert_eq!(a.word,if status==2 {7}else{9});}}}
#[test] fn all_correlations() {for field in 0..5 {let(s,mut c)=fixture();match field {0=>c.key.generation+=1,1=>c.key.input_generation+=1,2=>c.key.incarnation="other".into(),3=>c.key.iteration+=1,_=>c.key.attempt+=1};assert_eq!(accept_completion(&s,&c),None);}}
#[test] fn no_pending() {let(mut s,c)=fixture();s.pending=None;assert_eq!(accept_completion(&s,&c),None);}
#[test] fn wrong_phase() {for phase in [0,2] {let(mut s,c)=fixture();s.phase=phase;assert_eq!(accept_completion(&s,&c),None);}}
#[test] fn duplicate() {let(mut s,c)=fixture();s.committed.push(c.key.clone());assert_eq!(accept_completion(&s,&c),None);let(s,c)=fixture();let a=accept_completion(&s,&c).unwrap();assert_eq!(accept_completion(&a,&c),None);}
#[test] fn invalid_status() {let(s,mut c)=fixture();c.status=3;assert_eq!(accept_completion(&s,&c),None);}
}
'''

def main(run,narrow=False,expression=False):
    global PREFIX,SUFFIX
    if expression:
        PREFIX+='''if state.phase != 1 || state.pending.as_ref() != Some(&completion.key)
    || state.committed.contains(&completion.key) || completion.status > 2 { return None; }
let mut next=state.clone();
next.pending=None;next.committed.push(completion.key.clone());
next.phase=if completion.status==0 && state.remaining>0 {0}else{2};
// Publish the completion's word, retaining the existing word for trap.
if completion.status!=2 { next.word = '''
        SUFFIX='; }\nSome(next)\n'+SUFFIX
    elif narrow:
        PREFIX+='''if state.phase != 1 || state.pending.as_ref() != Some(&completion.key)
    || state.committed.contains(&completion.key) || completion.status > 2 { return None; }
let mut next = state.clone();
// Clear pending, append this key, set phase from status and remaining, publish word except trap.
'''
        SUFFIX='\nSome(next)\n'+SUFFIX
    run=Path(run);out=run/('formal-transaction/fim/publish-expression' if expression else ('formal-transaction/fim/narrowed' if narrow else 'formal-transaction/fim'));out.mkdir(parents=True,exist_ok=True)
    index=json.loads((run/'grown/stage-1-index.json').read_text())
    occurrence=next(m for m in index['members'] if m['kind']=='occurrence' and m['fields']['state']=='ready')
    owner=occurrence['semantic_id']
    op=next(m for m in index['members'] if m['kind']=='operation' and m['fields']['owner']==owner)
    graph=next(g for g in index['graphs'] if g['graph']==op['graph'])
    source=(PREFIX+'todo!()'+SUFFIX).encode();a=len(PREFIX.encode());b=a+len(b'todo!()');sha=hashlib.sha256(source).hexdigest()
    binding={'schema':'proposed-code-refinement-transaction-v1','subject':op['address'],'snapshot':graph['header']['snapshot-ref'],
      'lowering_profile':'authored checked-profile lowering scaffold; FIM publish-value expression' if expression else ('authored guard scaffold and FIM state-update span' if narrow else 'whole function body'),
      'semantic_scope':'completion acceptance subclaim under controller operation; helper is not yet a native admitted realization',
      'contract':op['fields']['contract'],'source_sha256':sha,'byte_range':[a,b],
      'required_gates':['exact-source','rust-tests','implementation-proof','runtime-atomic-commit'],
      'proof_scope':'pure function and later implementation/model correspondence','execution':'blocked'}
    save(out/'binding.json',binding);(out/'scaffold.rs').write_bytes(source)
    model=json.loads((ROOT/'config/model.json').read_text());props=json.load(urllib.request.urlopen(model['endpoint']+'/props',timeout=5))
    require(Path(props['model_path']).resolve()==Path(model['gguf']).resolve(),'checkpoint-path')
    require(hashlib.sha256(Path(model['gguf']).read_bytes()).hexdigest()==model['sha256'],'checkpoint-digest')
    logs=[];passed=False;previous=''
    for attempt in range(1,4):
        folder=out/str(attempt);folder.mkdir(exist_ok=True)
        guidance='' if not previous else '// Previous compiler/test feedback: '+previous[-1400:].replace('\n','\n// ')+'\n'
        prompt=serialize(guidance+PREFIX,SUFFIX)
        request={'prompt':prompt,'temperature':0,'n_predict':800,'stream':False,'stop':['<|endoftext|>','<|fim_prefix|>','<|fim_suffix|>','<|fim_middle|>','<|im_start|>','<|im_end|>']}
        save(folder/'request.json',request);(folder/'prompt.txt').write_text(prompt)
        req=urllib.request.Request(model['endpoint']+'/completion',data=json.dumps(request).encode(),headers={'Content-Type':'application/json'})
        response=json.load(urllib.request.urlopen(req,timeout=120));save(folder/'response.json',response)
        completion=response['content'];(folder/'completion.txt').write_text(completion)
        candidate=apply(source,sha,[a,b],completion);(folder/'candidate.rs').write_bytes(candidate)
        c=subprocess.run(['rustc','--edition=2021','--test',str(folder/'candidate.rs'),'-o',str(folder/'candidate-tests')],capture_output=True,text=True)
        previous=c.stdout+c.stderr;status=c.returncode
        if status==0:
            c=subprocess.run([str(folder/'candidate-tests')],capture_output=True,text=True);previous=c.stdout+c.stderr;status=c.returncode
        (folder/'checks.log').write_text(previous);passed=status==0
        row={'attempt':attempt,'candidate_sha256':hashlib.sha256(candidate).hexdigest(),'tests_passed':passed,'proof':'open','executable_admission':False};save(folder/'checks.json',row);logs.append(row)
        if passed:break
    expect=[]
    for name,expected in [('stale-source','Stale source digest'),('wrong-range','Invalid byte range')]:
        try:apply(source,'0'*64 if name=='stale-source' else sha,[a,b] if name=='stale-source' else [0,len(source)+1],'')
        except ValueError as e:require(str(e)==expected,'wrong-negative-category');expect.append({'case':name,'rejected':True})
        else:raise AssertionError(name)
    receipt={'subject':binding['subject'],'snapshot':binding['snapshot'],'source_sha256':sha,'checkpoint':model,
       'attempts':logs,'negative_checks':expect,'rustc':subprocess.check_output(['rustc','--version'],text=True).strip(),
       'tests_passed':passed,'implementation_proof':'open','native_proof_receipt':None,'runtime_atomic_commit':'open',
       'closure':{'candidate_inspectable':True,'executable_admission':False,'reason':'required implementation theorem and runtime correspondence absent'}}
    save(out/'transaction-receipt.json',receipt);print('FIM_TRANSACTION_RECORDED',out,'tests_passed=',passed)
if __name__=='__main__':main(sys.argv[1],narrow='--narrow' in sys.argv[2:],expression='--expression' in sys.argv[2:])
