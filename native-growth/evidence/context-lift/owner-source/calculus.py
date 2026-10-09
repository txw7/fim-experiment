"""Bounded construction IR: typed contexts, capture-free substitution, alpha/beta.

These are construction laws, not asserted laws of English or native SHG admission.
"""
from dataclasses import dataclass, asdict
import hashlib
import json

E, C, P, T, R = 'entity', 'predicative-content', 'proposition', 'temporal-parameter', 'temporal-reference'
def arrow(a, b): return ('arrow', a, b)
def type_text(t): return f'({type_text(t[1])} -> {type_text(t[2])})' if isinstance(t, tuple) else t

SIGNATURES = {
    'was': (('subject', E), ('complement', C), P),
    'is': (('subject', E), ('complement', C), P),
    'anchor-was': (('subject', E), ('complement', C), ('time', T), P),
    'what': (('abstraction', arrow(C, P)), C),
    'copular': (('subject', C), ('complement', C), P),
    'when-operator': (('target', P), ('anchor', arrow(T, P)), P),
    'when-relative': (('anchor', arrow(T, P)), R),
    'temporal-attach': (('target', P), ('temporal', R), P),
}

@dataclass(frozen=True)
class Term:
    kind: str
    name: str = ''
    type: object = None
    args: tuple = ()
    origin: str = ''

def var(name, typ, origin=''): return Term('var', name, typ, origin=origin)
def atom(name, typ, origin=''): return Term('atom', name, typ, origin=origin)
def lam(v, body, origin=''): return Term('abstract', v.name, v.type, (body,), origin)
def apply(f, x, origin=''): return Term('apply', args=(f,x), origin=origin)
def call(name, *args, origin=''): return Term('call', name, args=tuple(args), origin=origin)

def infer(term, env=None):
    env = {} if env is None else env
    if term.kind == 'atom': return term.type
    if term.kind == 'var':
        if term.name not in env: raise ValueError('unbound variable: '+term.name)
        if env[term.name] != term.type: raise TypeError('variable type mismatch: '+term.name)
        return term.type
    if term.kind == 'abstract':
        return arrow(term.type, infer(term.args[0], {**env, term.name:term.type}))
    if term.kind == 'apply':
        f, x = (infer(a, env) for a in term.args)
        if not isinstance(f, tuple) or f[0] != 'arrow' or f[1] != x:
            raise TypeError('application port mismatch')
        return f[2]
    sig = SIGNATURES[term.name]
    if len(term.args) != len(sig)-1: raise TypeError('arity mismatch: '+term.name)
    for a, (role, expected) in zip(term.args, sig[:-1]):
        if infer(a,env) != expected: raise TypeError(term.name+'/'+role)
    return sig[-1]

def free(term):
    if term.kind == 'var': return {term.name:term.type}
    found = {}
    for a in term.args:
        for name, typ in free(a).items():
            if name in found and found[name] != typ: raise TypeError('conflicting variable type')
            found[name] = typ
    if term.kind == 'abstract': found.pop(term.name,None)
    return found

def names(term):
    return ({term.name} if term.kind in {'var','abstract'} else set()) | set().union(*(names(a) for a in term.args))

def substitute(term, name, replacement):
    if term.kind == 'var' and term.name == name: return replacement
    if term.kind == 'abstract':
        if term.name == name or name not in free(term.args[0]): return term
        body, binder = term.args[0], term.name
        if binder in free(replacement):
            used = names(body) | names(replacement) | {name}
            i=0
            while f'{binder}_{i}' in used: i+=1
            fresh=f'{binder}_{i}'
            body=substitute(body,binder,var(fresh,term.type,term.origin))
            binder=fresh
        return lam(var(binder,term.type),substitute(body,name,replacement),term.origin)
    return Term(term.kind,term.name,term.type,tuple(substitute(a,name,replacement) for a in term.args),term.origin)

def alpha_key(term, bound=()):
    if term.kind == 'var':
        return ('bound',bound[::-1].index(term.name),term.type) if term.name in bound else ('free',term.name,term.type)
    if term.kind == 'abstract': return ('abstract',term.type,alpha_key(term.args[0],(*bound,term.name)))
    return (term.kind,term.name,term.type,tuple(alpha_key(a,bound) for a in term.args))

def normalize(term, env=None, limit=1000):
    env = free(term) if env is None else env
    typ = infer(term,env); events=[]
    def visit(t,address):
        args=tuple(visit(a,address+'/'+str(i)) for i,a in enumerate(t.args))
        t=Term(t.kind,t.name,t.type,args,t.origin)
        if t.kind=='apply' and args[0].kind=='abstract':
            if len(events)>=limit: raise ValueError('normalization step limit')
            fn,x=args; out=substitute(fn.args[0],fn.name,x)
            events.append({'law':'beta-capture-avoiding','address':address,'input':digest(t),'output':digest(out)})
            return visit(out,address)
        return t
    result=visit(term,'root')
    assert infer(result,env)==typ
    return result,events

def digest(term): return hashlib.sha256(json.dumps(asdict(term),sort_keys=True).encode()).hexdigest()
def tree(term, env=None, address='root'):
    env=free(term) if env is None else env
    info={'address':address,'kind':term.kind,'operator':term.name,'type':type_text(infer(term,env)),'origin':term.origin}
    if term.kind=='abstract':
        env={**env,term.name:term.type};roles=['body'];info['binder']={'id':term.name,'type':type_text(term.type)}
    elif term.kind=='call': roles=[r for r,t in SIGNATURES[term.name][:-1]]
    elif term.kind=='apply': roles=['function','argument']
    else: roles=[]
    info['children']=[{'role':r,'term':tree(a,env,address+'/'+r)} for r,a in zip(roles,term.args)]
    return info

def pretty(term, indent=0):
    pad=' '*indent
    if not term.args:
        return pad+('$'+term.name if term.kind=='var' else term.name)
    if term.kind=='abstract': head='abstract\n'+' '*(indent+2)+f'(${term.name} {type_text(term.type)})'
    else: head='apply' if term.kind=='apply' else term.name
    return pad+'('+head+'\n'+'\n'.join(pretty(a,indent+2) for a in term.args)+')'

def selfcheck():
    p,q=var('p',C),var('q',C)
    # Capture must rename the inner q, keeping the supplied q free.
    term=apply(lam(p,lam(q,call('copular',p,q))),q)
    result,events=normalize(term)
    assert free(result)=={'q':C}
    assert result.name!='q' and result.args[0].args[0].name=='q'
    assert alpha_key(result)==alpha_key(lam(var('r',C),call('copular',q,var('r',C))))
    assert alpha_key(lam(p,call('was',atom('she',E),p)))==alpha_key(lam(q,call('was',atom('she',E),q)))
    try: infer(apply(lam(p,call('was',atom('she',E),p)),atom('he',E)))
    except TypeError: pass
    else: raise AssertionError('ill-typed fill accepted')
    try: infer(var('missing',C))
    except ValueError: pass
    else: raise AssertionError('unbound variable accepted')
    assert normalize(result)[1]==[]
    return {'capture_avoidance':True,'alpha_equivalence':True,'type_rejection':True,'unbound_rejection':True,'normalization_idempotence':True,'beta_steps':len(events)}

if __name__=='__main__': print(json.dumps(selfcheck(),indent=2))
