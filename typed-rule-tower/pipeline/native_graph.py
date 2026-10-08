"""Run the pinned native reference seam and construct the VM semantic graph."""
import json, subprocess, time, hashlib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def literal(value):
    if isinstance(value, dict):
        return '('+' '.join(':'+k.replace('_','-')+' '+literal(v) for k,v in value.items())+')'
    if isinstance(value,list): return '('+' '.join(map(literal,value))+')'
    if value is None or value is False: return 'nil'
    if value is True: return 't'
    if isinstance(value,str): return '"'+value.replace('\\','\\\\').replace('"','\\"')+'"'
    return str(value)

def main():
    pins=json.loads((ROOT/'pins/sources.lock.json').read_text())
    native=Path(pins['sources']['goggles']['path'])
    for name,pin in pins['sources'].items():
        if not pin.get('selected'): continue
        actual=subprocess.check_output(['git','-C',pin['path'],'rev-parse','HEAD'],text=True).strip()
        if actual != pin['commit']: raise SystemExit(f'{name} pin drift')
    run=ROOT/'runs'/str(time.time_ns()); run.mkdir(parents=True)
    inputs={p.stem:json.loads(p.read_text()) for p in sorted((ROOT/'spec').glob('*.json'))}
    (run/'manifest.json').write_text(json.dumps({'pins':pins,'inputs':inputs,'scope':'reference lowering and native VM graph; no executable VM synthesis'},indent=2)+'\n')
    funcs=inputs['interfaces']['functions']
    calls={'run':['step'],'step':['fetch','decode','alu','memory-execution','control'],'alu':['register-read','register-write','flags'],'memory-execution':['register-read','register-write','memory-read','memory-write'],'control':['memory-read','memory-write']}
    accesses={'register-read':['registers'],'register-write':['registers'],'flags':['flags'],'memory-read':['memory'],'memory-write':['memory'],'fetch':['pc','memory'],'alu':['registers','flags','pc'],'memory-execution':['registers','memory','pc'],'control':['pc','sp','flags','memory'],'step':['registers','pc','sp','flags','memory'],'run':['registers','pc','sp','flags','memory']}
    rows=[{'caller':a,'callee':b} for a,bs in calls.items() for b in bs]
    (run/'vm-projection.json').write_text(json.dumps({'functions':funcs,'calls':rows,'state_access':accesses,'note':'call/state-access projection; instruction transitions remain authored specifications'},indent=2)+'\n')
    out=ROOT/'generated/graph'; out.mkdir(exist_ok=True)
    driver='(load '+literal(str(ROOT/'synthesis/load.lisp'))+')\n(in-package #:lsip)\n'
    seam=['protocol-graph->afsm-kernel-v1','realize-afsm-exec','lower-afsm-exec-to-compiler-ir','record-cfg-functions-from-ir2','lower-cfg-function-to-synth-slot-plan','lower-synth-slot-plan-to-ir1','dispatch-ir1-plan','placement-result-fragment-for-target']
    driver+="(defparameter *fim-observed* nil)\n(defparameter *fim-originals* nil)\n"
    for name in seam:
        driver+="(let ((original (symbol-function '"+name+"))) (push (cons '"+name+" original) *fim-originals*) (setf (symbol-function '"+name+") (lambda (&rest args) (push '"+name+" *fim-observed*) (apply original args))))\n"
    emitter=(native/'scripts/emit_l12_recursive_protocol_governor_v1.lisp').read_text()
    emitter=emitter[emitter.index('(defun l12b-emitter'):]
    emitter=emitter.replace('(uiop:command-line-arguments)',"(list "+' '.join(literal(str(run/p)) for p in ['reference-identities.sexp','reference.rs','reference-probes.txt'])+")")
    driver+=emitter+'\n(dolist (row *fim-originals*) (setf (symbol-function (car row)) (cdr row)))\n'
    driver+='(with-open-file (s '+literal(str(run/'observed-calls.txt'))+' :direction :output :if-exists :supersede) (dolist (name (reverse *fim-observed*)) (format s "~A~%" name)))\n'
    driver+='(defparameter *vm-inputs* \''+literal(inputs)+')\n'
    driver+='(defparameter *vm-functions* \''+literal(funcs)+')\n'
    driver+='(defparameter *vm-calls* \''+literal(rows)+')\n'
    driver+='(defparameter *vm-accesses* \''+literal([{'actor':a,'state':s} for a,ss in accesses.items() for s in ss])+')\n'
    driver+=r'''
(defun fim-write (path object)
  (with-open-file (s path :direction :output :if-exists :supersede)
    (let ((*print-readably* t) (*print-pretty* nil)) (write object :stream s) (terpri s))))
(let* ((root (make-semantic-region-v1 :semantic-ref "basic-vm" :region-kind :program-region :surface-ref *vm-inputs*))
       (regions (mapcar (lambda (f) (make-semantic-region-v1 :semantic-ref (getf f :id) :region-kind :function-region :surface-ref f :state-profile-ref (getf *vm-inputs* :state) :formal-surface-ref (getf *vm-inputs* :traps))) *vm-functions*))
       (states (mapcar (lambda (s) (make-semantic-node-v1 :semantic-ref s :node-kind :state-domain :state-profile-ref (getf *vm-inputs* :state))) '("registers" "pc" "sp" "flags" "memory")))
       (ports (loop for r in regions append (loop for direction in '(:in :out) collect (make-semantic-port-v1 :owner-region-ref r :port-kind :data :direction direction :semantic-ref (format nil "~A.~A" (semantic-region-v1-semantic-ref r) direction) :contract-ref (semantic-region-v1-surface-ref r)))))
       (edges nil))
  (labels ((region (id) (or (find id regions :key #'semantic-region-v1-semantic-ref :test #'equal) (error "Unknown function ~A" id)))
           (inc (role kind obj) (make-semantic-incidence-v1 :role role :participant-kind kind :participant-ref obj))
           (edge (kind constitution incidences) (push (make-semantic-hyperedge-v1 :relation-kind kind :constitution-ref constitution :incidences incidences) edges)))
    (dolist (r regions) (edge :containment :containment-v1 (list (inc :container :region root) (inc :member :region r))))
    (dolist (row *vm-calls*) (edge :call :call-v1 (list (inc :caller :region (region (getf row :caller))) (inc :callee :region (region (getf row :callee))) (make-semantic-incidence-v1 :role :argument :participant-kind :port :participant-ref (find (format nil "~A.IN" (getf row :callee)) ports :key #'semantic-port-v1-semantic-ref :test #'equal) :ordinal 0))))
    (dolist (row *vm-accesses*) (edge :state-access :state-access-v1 (list (inc :actor :region (region (getf row :actor))) (inc :state :node (find (getf row :state) states :key #'semantic-node-v1-semantic-ref :test #'equal)))))
    (dolist (state states) (edge :state-ownership :state-ownership-v1 (list (inc :owner :region root) (inc :state :node state))))
    (dolist (pair '(("fetch" "decode") ("decode" "alu") ("decode" "memory-execution") ("decode" "control")))
      (edge :dataflow :dataflow-v1 (list (inc :source :port (find (format nil "~A.OUT" (first pair)) ports :key #'semantic-port-v1-semantic-ref :test #'equal)) (inc :target :port (find (format nil "~A.IN" (second pair)) ports :key #'semantic-port-v1-semantic-ref :test #'equal)))))
    (let* ((graph (make-recursive-semantic-hypergraph-v1 :graph-kind :basic-vm :regions (cons root regions) :nodes states :ports ports :hyperedges edges :root-region-ref root))
           (index (semantic-address-index-v1 graph)))
      (dolist (binding (semantic-address-index-v1-bindings index))
        (let* ((address (semantic-address-binding-v1-exact-address binding))
               (restored (restore-semantic-address-wire-v1 (semantic-address-wire-v1 address)))
               (resolved (semantic-address-resolution-v1-resolved-object-ref (resolve-semantic-address-v1 restored graph))))
          (unless (equal (semantic-hypergraph-ref-identity-v1 resolved) (semantic-hypergraph-ref-identity-v1 (semantic-address-binding-v1-object-ref binding))) (error "Occurrence address mismatch kind=~S expected=~S resolved=~S" (semantic-address-binding-v1-object-kind binding) (semantic-hypergraph-ref-identity-v1 (semantic-address-binding-v1-object-ref binding)) (semantic-hypergraph-ref-identity-v1 resolved)))))
'''
    driver+='(fim-write '+literal(str(out/'vm-native.sexp'))+' (recursive-semantic-hypergraph-v1-form graph))\n'
    driver+='(fim-write '+literal(str(out/'vm-addresses.sexp'))+' index)\n'
    driver+='(format t "VM_NATIVE_GREEN regions=~D states=~D ports=~D edges=~D addresses=~D~%" (length (cons root regions)) (length states) (length ports) (length edges) (length (semantic-address-index-v1-bindings index))))))\n'
    (run/'driver.lisp').write_text(driver)
    with (run/'native.log').open('w') as log:
        result=subprocess.run(['sbcl','--script',str(run/'driver.lisp')],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
    if (run/'observed-calls.txt').exists():
        (run/'call-graph.json').write_text(json.dumps({'observed_native_calls':(run/'observed-calls.txt').read_text().splitlines(),'source':'runtime function wrappers'},indent=2)+'\n')
    checks={'native':result.returncode}
    if result.returncode == 0:
        source=(run/'reference.rs').read_text()
        source+='\nfn main() {\n'
        seen=set()
        for line in (run/'reference-probes.txt').read_text().splitlines():
            label,start,event,end=line.split()
            if label not in seen:
                source+=f'let mut {label}_state: i32 = {start};\n'; seen.add(label)
            source+=f'assert_eq!({label}_state,{start}); {label}_state=step({label}_state,{event}); assert_eq!({label}_state,{end});\n'
        source+='}\n'; (run/'reference-exec.rs').write_text(source)
        with (run/'rust-check.log').open('w') as log:
            compile_result=subprocess.run(['rustc','--edition=2021',str(run/'reference-exec.rs'),'-o',str(run/'reference-exec')],stdout=log,stderr=subprocess.STDOUT)
            checks['reference_compile']=compile_result.returncode
            if compile_result.returncode == 0: checks['reference_probes']=subprocess.run([str(run/'reference-exec')],stdout=log,stderr=subprocess.STDOUT).returncode
        (run/'checks.json').write_text(json.dumps(checks,indent=2)+'\n')
        artifacts=[run/'reference-identities.sexp',run/'reference.rs',out/'vm-native.sexp',out/'vm-addresses.sexp']
        (run/'artifact-digests.json').write_text(json.dumps({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in artifacts},indent=2)+'\n')
    status={'returncode':result.returncode,'native_log':str(run/'native.log'),'vm_executable_lowering':'not implemented','formal_acceptance':'unresolved'}
    (run/'stages.json').write_text(json.dumps(status,indent=2)+'\n')
    print(run,flush=True)
    raise SystemExit(0 if checks and all(value == 0 for value in checks.values()) else 1)
if __name__=='__main__': main()
