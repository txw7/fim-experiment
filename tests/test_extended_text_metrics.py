import collections,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'scripts'))
from extended_text_metrics import compare,distribution_metrics
c=collections.Counter(a=2,b=2)
r=compare(c,c);assert r['js_bits']==0 and r['kl_p_q_bits']==0
r=compare(collections.Counter(a=10),collections.Counter(b=10));assert 0<r['js_bits']<=1
r=distribution_metrics(c,collections.Counter({('a','b'):2,('b','a'):2}))
assert r['entropy_bits']==1 and r['next_given_previous_entropy_bits']==0 and r['adjacent_mutual_information_bits']==1
print('Extended metric checks passed.')
