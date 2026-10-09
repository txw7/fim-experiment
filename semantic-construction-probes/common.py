"""Local persistence and HTTP helpers; no semantic admission authority."""
import hashlib,json,os,urllib.request
from pathlib import Path
NATIVE=Path(os.environ.get('SEMALG_NATIVE_ROOT','/home/user0/ORCHESTRATION/worktrees/goggles-semantic-lift-v1'))
def sha(data):return hashlib.sha256(data).hexdigest()
def atomic_text(path,text):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
 temp=path.with_suffix(path.suffix+'.tmp')
 with open(temp,'w') as s:
  os.chmod(temp,0o600);s.write(text);s.flush();os.fsync(s.fileno())
 os.replace(temp,path)
def save(path,value):atomic_text(path,json.dumps(value,indent=2,ensure_ascii=False)+'\n')
def post(url,body):
 req=urllib.request.Request(url,json.dumps(body).encode(),{'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=120) as resp:return json.load(resp)
def sexp(value):
 if isinstance(value,dict):return '('+' '.join(':'+k.replace('_','-')+' '+sexp(v) for k,v in value.items())+')'
 if isinstance(value,list):return '('+' '.join(map(sexp,value))+')'
 if value is None:return 'nil'
 if isinstance(value,str):return '\"'+value.replace('\\','\\\\').replace('\"','\\\"')+'\"'
 return str(value)
