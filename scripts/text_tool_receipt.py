"""Record local acquisition state without equating downloads with execution."""
import hashlib,importlib.metadata,json,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'working/text-primitives';deps=root/'deps/text-tools'
origins={'TAACO':'https://github.com/LCR-ADS-Lab/TAACO','text-pair':'https://github.com/ARTFL-Project/text-pair','zeuscansion':'https://github.com/manexagirrezabal/zeuscansion','xl-lexeme':'https://github.com/pierluigic/xl-lexeme','cooccure':'https://github.com/mohsaqr/cooccure','bibnets':'https://github.com/mohsaqr/bibnets'}
repos=[]
for name,url in origins.items():
 p=deps/name;commit=subprocess.check_output(['git','-C',str(p),'rev-parse','HEAD'],text=True).strip()
 repos.append(dict(name=name,url=url,path=str(p),commit=commit,status='source obtained'))
archives=[]
for p in sorted((deps/'packages').iterdir()):
 if p.is_file():archives.append(dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),status='archive obtained'))
packages=[]
for name in ['scipy','networkx','rapidfuzz','nltk','morfessor','sacrebleu','scikit-learn','spacy','gensim','rakun2','grakel','powerlaw','pronouncing','en-core-web-sm']:
 packages.append(dict(name=name,version=importlib.metadata.version(name),status='installed'))
checked=[]
for p in out.iterdir():
 if p.name in {'extended-metrics.json','tool-smoke.json','morphology-receipt.json','taaco-smoke.csv','optional-tool-checks.json','morphemes.jsonl','morfessor.bin'}:
  checked.append(dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
receipt=dict(schema='text-tool-acquisition-v1',python=sys.version,environment=str(root/'working/text-tools-venv'),
 repositories=repos,packages=packages,archives=archives,lexical_data=json.loads((deps/'nltk-data/receipt.json').read_text()),
 runtime_artifacts=checked,optional_import_checks=json.loads((out/'optional-tool-checks.json').read_text()),
 unresolved=[dict(tool='TRACER',reason='published vcs.etrap.eu source host does not resolve'),
 dict(tool='SPARSAR',reason='published Ubuntu link returns Google sign-in, not program'),
 dict(tool='Scandroid',reason='published author page returns HTTP 404'),
 dict(tool='HalluGraph',reason='no public implementation identified in the primary paper')],
 not_activated=['R runtime for cooccure/bibnets','TextPAIR PostgreSQL deployment','foma/hunpos for ZeuScansion','XL-LEXEME weights (2239700717 bytes)','KinGBERT neural dependencies and embedding weights','benepar constituency model','amrlib AMR model'],
 no_student_training=True,no_gpu_model_loading=True)
(out/'tool-acquisition.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(dict(packages=len(packages),source_repositories=len(repos),archives=len(archives),lexical_archives=len(receipt['lexical_data']),unresolved=len(receipt['unresolved']))))
