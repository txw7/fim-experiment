"""Fetch the official plaintext lexical archives, recording content hashes."""
import hashlib,json,urllib.request
from pathlib import Path
root=Path(__file__).resolve().parents[1]/'deps/text-tools/nltk-data';root.mkdir(parents=True,exist_ok=True)
rows=[]
for category,name in [('corpora','wordnet'),('corpora','omw-1.4'),('corpora','cmudict'),('tokenizers','punkt_tab')]:
    url=f'https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/{category}/{name}.zip'
    path=root/category/(name+'.zip');path.parent.mkdir(exist_ok=True)
    with urllib.request.urlopen(url,timeout=60) as response:data=response.read()
    assert data[:2]==b'PK', 'Expected a ZIP archive'
    path.write_bytes(data);rows.append(dict(name=name,url=url,path=str(path),bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
(root/'receipt.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
