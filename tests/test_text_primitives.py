import importlib.util,json,tempfile,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'scripts'))
spec=importlib.util.spec_from_file_location('primitives',Path(__file__).parents[1]/'scripts/text_primitives.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
with tempfile.TemporaryDirectory() as d:
 docs=[{'id':'a','family':'test','text':'not true and true','source_ref':{}},{'id':'b','family':'test','text':'false or true','source_ref':{}}];m=p.analyze(docs,d,window=1,min_count=1);assert m['tokens']==7 and m['pair_events']==10
 terms={r['term']:r for r in map(json.loads,(Path(d)/'terms.jsonl').read_text().splitlines())};assert terms['true']['count']==3 and terms['true']['document_frequency']==2;assert 'not' in terms and 'or' in terms
 pairs={tuple(r['terms']):r for r in map(json.loads,(Path(d)/'association.jsonl').read_text().splitlines())};assert ('true','false') not in pairs # cannot cross document boundaries
 assert pairs[('not','true')]['count']==1;assert all(r['ppmi']>=0 for r in pairs.values())
 grams=list(map(json.loads,(Path(d)/'ngrams-2.jsonl').read_text().splitlines()));assert any(r['tokens']==['false','or'] for r in grams)
print('Text primitive checks passed')

a=p.association(2,4,6,20);b=p.association(2,6,4,20)
assert a["lift"]==b["lift"] and a["confidence"]!=b["confidence"]
assert a["llr"]>=0
