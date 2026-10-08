#[cfg(kani)]
mod verification {
 use super::*;
 #[kani::proof]
 #[kani::unwind(12)]
 fn completion_contract() {
  let key=Key{generation:kani::any(),input_generation:kani::any(),incarnation:if kani::any(){"a".into()}else{"b".into()},iteration:kani::any(),attempt:kani::any()};
  let other=Key{generation:kani::any(),input_generation:kani::any(),incarnation:if kani::any(){"a".into()}else{"b".into()},iteration:kani::any(),attempt:kani::any()};
  let phase:u8=kani::any();kani::assume(phase<=2);
  let budget:u32=kani::any();kani::assume(budget<=2);
  let pending=if phase==1 {Some(key.clone())}else{None};
  let committed=if kani::any() {vec![key.clone()]}else{vec![]};
  let state=State{phase,remaining:budget,pending,committed,word:kani::any()};
  let completion=Completion{key:other,status:kani::any(),word:kani::any()};
  let allowed=state.phase==1 && state.pending.as_ref()==Some(&completion.key)
      && !state.committed.contains(&completion.key) && completion.status<=2;
  let actual=accept_completion(&state,&completion);
  assert_eq!(actual.is_some(),allowed);
  if let Some(next)=actual {
    assert_eq!(next.remaining,state.remaining);
    assert_eq!(next.pending,None);
    assert_eq!(next.committed.len(),state.committed.len()+1);
    assert_eq!(&next.committed[..state.committed.len()],&state.committed[..]);
    assert_eq!(next.committed.last(),Some(&completion.key));
    assert_eq!(next.phase,if completion.status==0 && budget>0 {0}else{2});
    assert_eq!(next.word,if completion.status==2 {state.word}else{completion.word});
  }
 }
}
