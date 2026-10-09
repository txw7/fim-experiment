import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import connectivity_student as c

def test_repeated_operand_uses_bind_one_identity():
 g=c.Graph();g.top=[g.tree(('AND',['a','a']))];graph=g.finish();c.targets(graph)
 uses=[e for e in graph['edges'] if e['role']=='binding']
 assert len(uses)==2 and uses[0]['source']!=uses[1]['source'] and uses[0]['target']==uses[1]['target']
 operands=[e for e in graph['edges'] if e['role']=='operand']
 assert [e['position'] for e in operands]==[0,1] and len({e['target'] for e in operands})==2

def test_source_topology_order_scope_and_cross_paragraph_identity():
 g=c.source_graph();ids={n['id']:i for i,n in enumerate(g['nodes'])};edges=g['edges']
 assert any(e['source']==ids['architecture'] and e['target']==ids['architecture/1'] and e['role']=='body' for e in edges)
 assert any(e['source']==ids['architecture/1/0'] and e['target']==ids['architecture/1'] and e['role']=='scope' for e in edges)
 assert any(e['source']==ids['alias:B1'] and e['target']==ids['identity:A'] and e['role']=='target' for e in edges)
 assert any(e['source']==ids['flow:0'] and e['target']==ids['identity:A'] and e['role']=='source' for e in edges)
 assert any(e['source']==ids['operator:once'] and e['target']==ids['event:commit'] and e['role']=='operand' for e in edges)
 assert any(e['source']==ids['operator:unavailable-gate'] and e['target']==ids['operator:open-and-no-positive'] and e['role']=='consequent' for e in edges)
 for node in g['nodes']:
  for span in node['spans']:assert g['source'][span['start']:span['end']]==span['quote']
 c.targets(g);tokens,positions=c.serial(g);assert len(positions)==len(g['nodes']) and len(tokens)<512

def test_split_excludes_isomorphic_compositions_and_ambiguous_targets():
 train,val,test=c.controls();groups=[{g['composition_signature'] for g in xs} for xs in [train,val,test]]
 assert groups[0].isdisjoint(groups[1]|groups[2]) and groups[1].isdisjoint(groups[2])
 for xs in [train,val,test]:
  for g in xs:c.targets(g);c.serial(g)

def test_binding_and_nesting_survive_serialization():
 def build(tree):
  g=c.Graph();g.top=[g.tree(tree)];return c.serial(g.finish())[0]
 assert build(('NOT',[('AND',['a','b'])]))!=build(('AND',[('NOT',['a']),'b']))
 assert build(('PAIR',['a','a']))!=build(('PAIR',['a','b']))
