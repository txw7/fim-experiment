"""Bounded leaf experiment; authored refinement, local FIM, no native admission."""
import hashlib
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'typed-rule-tower-v2/pipeline'))
from apply_candidate import apply
from serialize_fim import serialize

def digest(data):
    return hashlib.sha256(data).hexdigest()

def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')

PREFIX = '''// Proposed read_register contract: 8 u32 registers; index is u8.
// Return the indexed value for index < 8, otherwise InvalidRegister(index).
// No mutation, panic, wrapping index, or default value. Generate only the body.
#[derive(Debug, PartialEq, Eq)]
pub enum Trap { InvalidRegister(u8) }
pub struct Cpu { pub registers: [u32; 8] }
impl Cpu {
    pub fn read_register(&self, index: u8) -> Result<u32, Trap> {
'''
SUFFIX = '''
    }
}
#[cfg(test)] mod tests {
    use super::*;
    #[test] fn all_indices_and_preservation() {
        for values in [[0; 8], [u32::MAX; 8], [0, 1, 2, 3, 0x80000000, 7, 99, u32::MAX]] {
            let cpu = Cpu { registers: values };
            for index in 0..=u8::MAX {
                let expected = if index < 8 { Ok(values[index as usize]) }
                    else { Err(Trap::InvalidRegister(index)) };
                assert_eq!(cpu.read_register(index), expected);
                assert_eq!(cpu.registers, values);
            }
        }
    }
}
'''

def main(out):
    out.mkdir(parents=True, exist_ok=False)
    view_path = ROOT / 'native-growth/evidence/joint-growth/view.json'
    view_bytes = view_path.read_bytes()
    view = json.loads(view_bytes)
    matches = [n for n in view['nodes'] if n['label'] == ':REGISTER-READ'
               and n['registry'] == 'member-registry-v1' and n['scope'] == 'parent']
    if len(matches) != 1:
        raise ValueError('Ambiguous or missing native subject')
    node = matches[0]
    header = next(h for h in view['headers'] if h['scope'] == node['scope'])
    source = (PREFIX + 'todo!()' + SUFFIX).encode()
    span = [len(PREFIX.encode()), len(PREFIX.encode()) + len(b'todo!()')]
    binding = {'schema': 'proposed-register-leaf-refinement-v1',
               'native_subject': node, 'native_header': header,
               'view_sha256': digest(view_bytes),
               'contract': {'register_count': 8, 'value_type': 'u32', 'index_type': 'u8',
                            'valid': 'return registers[index]',
                            'invalid': 'return InvalidRegister(index)', 'writes': []},
               'contract_origin': 'authored proposed refinement of OPEN native interface',
               'lowering': 'authored Rust profile; not native graph lowering',
               'source_sha256': digest(source), 'body_byte_range': span,
               'native_admission': False, 'proof': 'OPEN'}
    save(out / 'binding.json', binding)
    (out / 'scaffold.rs').write_bytes(source)
    config = json.loads(Path('/home/user0/FIM/config/model.json').read_text())
    props = json.load(urllib.request.urlopen(config['endpoint'] + '/props', timeout=5))
    if Path(props['model_path']).resolve() != Path(config['gguf']).resolve():
        raise ValueError('Wrong checkpoint path')
    if digest(Path(config['gguf']).read_bytes()) != config['sha256']:
        raise ValueError('Wrong checkpoint digest')
    token_request = urllib.request.Request(config['endpoint'] + '/tokenize',
        data=json.dumps({'content': '<|fim_prefix|><|fim_suffix|><|fim_middle|>',
                         'add_special': False, 'parse_special': True}).encode(),
        headers={'Content-Type': 'application/json'})
    tokens = json.load(urllib.request.urlopen(token_request, timeout=5))
    save(out / 'tokenizer.json', tokens)
    if tokens['tokens'] != config['fim_token_ids']:
        raise ValueError('Wrong native FIM tokenization')
    prompt = serialize(PREFIX, SUFFIX)
    request = {'prompt': prompt, 'temperature': 0, 'n_predict': 160, 'stream': False,
               'stop': ['<|endoftext|>', '<|fim_prefix|>', '<|fim_suffix|>',
                        '<|fim_middle|>', '<|im_start|>', '<|im_end|>']}
    save(out / 'request.json', request)
    (out / 'prompt.txt').write_text(prompt)
    req = urllib.request.Request(config['endpoint'] + '/completion',
        data=json.dumps(request).encode(), headers={'Content-Type': 'application/json'})
    response = json.load(urllib.request.urlopen(req, timeout=120))
    save(out / 'response.json', response)
    completion = response['content']
    (out / 'completion.txt').write_text(completion)
    candidate = apply(source, binding['source_sha256'], span, completion)
    (out / 'candidate.rs').write_bytes(candidate)
    # Only the selected body may change; suffix includes the verification harness.
    assert candidate[:span[0]] == source[:span[0]]
    assert candidate[span[0] + len(completion.encode()):] == source[span[1]:]
    checks = []
    for name, sha, cut, expected in [
        ('stale-source', '0' * 64, span, 'Stale source digest'),
        ('out-of-range', digest(source), [0, len(source) + 1], 'Invalid byte range')]:
        try:
            apply(source, sha, cut, completion)
        except ValueError as error:
            assert str(error) == expected
            checks.append({'case': name, 'rejected': True, 'category': str(error)})
        else:
            raise AssertionError(name)
    compile_result = subprocess.run(['rustc', '--edition=2021', '--test',
        str(out / 'candidate.rs'), '-o', str(out / 'candidate-tests')],
        capture_output=True, text=True, timeout=30)
    log = compile_result.stdout + compile_result.stderr
    passed = False
    if compile_result.returncode == 0:
        result = subprocess.run([str(out / 'candidate-tests')], capture_output=True,
                                text=True, timeout=10)
        log += result.stdout + result.stderr
        passed = result.returncode == 0
    (out / 'checks.log').write_text(log)
    receipt = {'model': config, 'subject_address': node['address'],
               'snapshot': header['snapshot'], 'source_sha256': digest(source),
               'candidate_sha256': digest(candidate), 'negative_checks': checks,
               'rustc': subprocess.check_output(['rustc', '--version'], text=True).strip(),
               'tests_passed': passed,
               'test_scope': 'all 256 u8 indices on three register states; preservation',
               'implementation_proof': 'OPEN', 'native_refinement_admission': False,
               'executable_admission': False,
               'artifacts': {p.name: digest(p.read_bytes()) for p in out.iterdir()
                             if p.is_file() and p.name != 'candidate-tests'}}
    save(out / 'receipt.json', receipt)
    print(json.dumps(receipt, indent=2))
    if not passed:
        raise SystemExit(1)

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
