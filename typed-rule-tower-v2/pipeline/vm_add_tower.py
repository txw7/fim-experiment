"""Bounded native SHG refinement tower → source boundaries → raw local FIM."""
import hashlib, json, os, pathlib, subprocess, time, urllib.request
from native_graph import literal
from serialize_fim import serialize
from apply_candidate import apply
ROOT = pathlib.Path(__file__).resolve().parents[1]
NATIVE = pathlib.Path('/home/user0/ORCHESTRATION/worktrees/literate-goggles-pr192-33d30ba0')
ROUTER = pathlib.Path('/home/user0/ORCHESTRATION/worktrees/egress-stacks-pr46-ca96fc33/synthesis/stack-router')
TYPES = ['state','fetch-result','decode-result','vm-result','cpu','index','word-result','add-result','write-result']

def kw(x): return ':'+x

def lisp(x):
    if isinstance(x, str) and x.startswith(':'): return x.upper()
    if isinstance(x, dict): return '('+' '.join(kw(k.replace('_','-'))+' '+lisp(v) for k,v in x.items())+')'
    if isinstance(x, list): return '('+' '.join(map(lisp,x))+')'
    return literal(x)

def graph(name, nodes, links, generation):
    ports=[]; operations=[]; node_types=[]; placements=[]
    for node, inputs, outputs in nodes:
        ids=[]
        for direction, fields in [('in',inputs),('out',outputs)]:
            for port, typ in fields:
                key=f'{node}-{port}';ids.append(kw(key))
                ports.append(dict(id=kw(key),direction=kw(direction),value_type=kw(typ),effects=[':state-effect'],contract=':vm-contract'))
        posts={'step':[':trap-atomic-state', ':add-wrap-u32-nzcv-pc-plus-eight'], 'fetch':[':read-eight-bytes', ':checked-pc-plus-eight'], 'decode':[':opcode-one-add'], 'execute':[':trap-atomic-state'], 'unpack':[':outputs-only-on-success'], 'read-left':[':checked-register-index-16', ':read-only'], 'read-right':[':checked-register-index-16', ':read-only'], 'add':[':wrapping-u32-nzcv'], 'write':[':checked-destination-16'], 'flags':[':nzcv'], 'commit':[':publish-successor-only']}
        operations.append(dict(id=kw(node),inputs=[kw(f'{node}-{p}') for p,t in inputs],outputs=[kw(f'{node}-{p}') for p,t in outputs],preconditions=[],postconditions=posts[node],effects=[':state-effect'],contract=':vm-contract'))
        node_types.append(dict(id=kw(node+'-node'),ports=ids,operations=[kw(node)],machine=':unbound',contract=':vm-contract'))
        placements.append(dict(id=kw(node),type=kw(node+'-node'),parent=':none',state=':unbound',memory=':unbound',provider=':unbound',child=None))
    return dict(schema=':shg-declarations-v1',id=kw(name),generation=generation,source_ref=':vm-add-slice-v1',limits=dict(max_depth=4,max_occurrences=32,max_relations=512,max_input_nodes=4096),
        types=[dict(id=kw(t),schema=({'state':[':vm-state', ':registers',16,':word-bits',32,':pc-bits',32,':memory-bytes',65536], 'cpu':[':cpu',':registers',16,':word-bits',32,':flags',':nzcv'], 'index':[':unsigned-index',8], 'fetch-result':[':result',':state-plus-eight-bytes-next-pc',':trap'], 'decode-result':[':result',':state-plus-add-instruction-next-pc',':trap'], 'vm-result':[':result',':successor-state',':trap'], 'word-result':[':result',':u32',':trap'], 'add-result':[':result',':u32-plus-carry-overflow',':trap'], 'write-result':[':result',':private-working-state-plus-add-result',':trap']}[t]),refinements=[]) for t in TYPES],
        effects=[dict(id=':state-effect',input=':state',output=':state',constraints=[])],
        contracts=[dict(id=':vm-contract',assume=[],guarantee=[],invariants=[],effects=[':state-effect'],dependencies=[])],
        port_definitions=ports,node_types=node_types,machines=[],operations=operations,memory=[],bindings=[],placements=placements,
        connections=[dict(id=kw(f'flow-{i}'),type=':association',ends=[dict(role=':source',placement=kw(a),port=kw(f'{a}-{ap}')),dict(role=':target',placement=kw(b),port=kw(f'{b}-{bp}'))],contract=':vm-contract',effects=[':state-effect'],handler=':unbound') for i,(a,ap,b,bp) in enumerate(links)],children=[])

def child(parent, node, interior, mapping):
    next(p for p in parent['placements'] if p['id']==kw(node))['child']=kw(node+'-body')
    parent['children'].append(dict(id=kw(node+'-body'),declaration=interior,boundary_map=[dict(outer=kw(f'{node}-{outer}'),inner_placement=kw(inner),inner_port=kw(f'{inner}-{port}')) for outer,inner,port in mapping]))

STEP=[('step',[('state','state')],[('result','vm-result')])]
NETWORK=[('fetch',[('state','state')],[('packet','fetch-result')]),('decode',[('packet','fetch-result')],[('decoded','decode-result')]),('execute',[('decoded','decode-result')],[('result','vm-result')])]
ALU=[('unpack',[('decoded','decode-result')],[('cpu','cpu'),('lhs','index'),('rhs','index'),('context','decode-result')]),
 ('read-left',[('cpu','cpu'),('index','index')],[('word','word-result')]),('read-right',[('cpu','cpu'),('index','index')],[('word','word-result')]),
 ('add',[('lhs','word-result'),('rhs','word-result')],[('sum','add-result')]),
 ('write',[('context','decode-result'),('sum','add-result')],[('written','write-result')]),
 ('flags',[('written','write-result')],[('flagged','write-result')]),('commit',[('flagged','write-result')],[('result','vm-result')])]
ALU_LINKS=[('unpack','cpu','read-left','cpu'),('unpack','cpu','read-right','cpu'),('unpack','lhs','read-left','index'),('unpack','rhs','read-right','index'),('read-left','word','add','lhs'),('read-right','word','add','rhs'),('unpack','context','write','context'),('add','sum','write','sum'),('write','written','flags','written'),('flags','flagged','commit','flagged')]

def declarations():
    stages=[]
    for generation in range(3):
        root=graph('vm',STEP,[],generation)
        if generation:
            network=graph('step-body',NETWORK,[('fetch','packet','decode','packet'),('decode','decoded','execute','decoded')],generation)
            if generation==2:
                alu=graph('add-body',ALU,ALU_LINKS,generation)
                child(network,'execute',alu,[('decoded','unpack','decoded'),('result','commit','result')])
            child(root,'step',network,[('state','fetch','state'),('result','execute','result')])
        stages.append(root)
    return stages

def command(args, log, **kwargs):
    with log.open('w') as out: subprocess.run(args,stdout=out,stderr=subprocess.STDOUT,check=True,**kwargs)

def main():
    run=ROOT/'runs/vm-add-tower'/str(time.time_ns());run.mkdir(parents=True)
    (run/'declarations.sexp').write_text(lisp(declarations())+'\n')
    profile=json.loads((ROOT/'spec/profile.json').read_text());assert (profile['register_count'],profile['word_bits'],profile['instruction_bytes'],profile['pc_advance_bytes'],profile['overflow'],profile['trap_commit'])==(16,32,8,8,'wrapping arithmetic; flags NZCV','no CPU or memory mutations committed on a trap'), 'Unsupported profile';(run/'profile.json').write_text(json.dumps(profile,indent=2)+'\n')
    command(['sbcl','--script',str(ROOT/'synthesis/vm_add_tower.lisp'),str(run/'declarations.sexp'),str(run)],run/'native.log')
    print('Native tower:',run,flush=True)
    metadata=json.loads(subprocess.check_output(['cargo','metadata','--format-version','1','--no-deps','--manifest-path',str(ROUTER/'Cargo.toml')],text=True))
    command(['cargo','build','--locked','--manifest-path',str(ROUTER/'Cargo.toml'),'-p','stack-router-registry-kernel','--example','h002_file_lookup'],run/'router-build.log')
    binary=pathlib.Path(metadata['target_directory'])/'debug/examples/h002_file_lookup';receipts=[]
    for stage in range(3):
        rows=json.loads((run/f'stage-{stage}-exports.json').read_text())
        for row in rows:
            path=run/'selected-export.json';path.write_text(json.dumps([row]))
            result=json.loads(subprocess.check_output([str(binary),str(path)],text=True))
            assert result['selected_address_ref']==row['address_ref_ascii'] and not result['executable_realization_admitted']
            receipts.append(dict(stage=stage,address=row['address_ref_ascii'],status=result['status'],receipt=result))
    (run/'routes.json').write_text(json.dumps(receipts,indent=2)+'\n')
    print('R001 routed addresses:',len(receipts),flush=True)
    realize(run)
    print('DEMO_GREEN',run,flush=True)

# Rust realization is a bounded adapter, not a general compiler or proof admission.
if __name__=='__main__':
    from vm_add_realize import realize
    main()
