from local_constructions import substrate,verify
from typed_local import validate
c={'id':'probe','reading':'probe','objects':substrate('what she was'),'relations':[]}
v=verify(c,'what she was');assert v['source_preserved'];assert v['uninterpreted_operators'];assert v['construction_obligations']
c['objects'][0]['type']='changed';assert not verify(c,'what she was')['source_preserved']
x={'reading':'probe','applications':[{'id':'a','operator':'candidate','anchors':['t0'],'construction':'claim','ports':[{'id':'p','role':'arg','value_type':'unknown','filler':'a'}],'result_type':'unknown'}],'positions':[],'bindings':[],'networks':[],'relations':[],'unresolved':[]}
v=validate(x,'what she was');assert 'self argument p' in v['errors'];assert 'application/containment cycle' in v['errors'];assert not v['structural_gate']
print('Immutable source, omission, missing construction, self-argument and cycle checks passed')
