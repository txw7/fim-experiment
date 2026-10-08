// Pure completion acceptance, proposed leaf realization under the addressed controller operation.
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
todo!()
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
