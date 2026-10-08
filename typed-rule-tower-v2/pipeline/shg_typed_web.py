import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
run=Path(sys.argv[1]);data={'index':json.loads((run/'grown/stage-1-index.json').read_text()),'rule':json.loads((run/'generated-rule.json').read_text()),'environment':json.loads((run/'binding-environment.json').read_text()),'trace':json.loads((run/'runtime-transition-trace.json').read_text()),'result':json.loads((run/'result.json').read_text()),'delta':json.loads((run/'graph-delta.json').read_text())}
(run/'network.html').write_text((ROOT/'visuals/typed-web-template.html').read_text().replace('DATA_PLACEHOLDER',json.dumps(data,separators=(',',':')).replace('<','\\u003c')))
print(run/'network.html')
