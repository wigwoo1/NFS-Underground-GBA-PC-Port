"""Exact closed publication comparison at common original refreshes."""
import json,sys,hashlib
from pathlib import Path
a=json.loads(Path(sys.argv[1]).read_text());b=json.loads(Path(sys.argv[2]).read_text());old={x['refresh']:x for x in a['model_scene_captures']};checks=[]
for x in b['model_scene_captures']:
 assert x['refresh'] in old
 for k in ('frame','graph','supplements','builders','current-sources'):
  left=Path(old[x['refresh']][k]).read_bytes();right=Path(x[k]).read_bytes();assert left==right,(x['refresh'],k)
  checks.append(dict(refresh=x['refresh'],section=k,bytes=len(right),sha256=hashlib.sha256(right).hexdigest()))
assert checks
out=dict(exact_sections=len(checks),checks=checks,scope='complete immutable publication bytes at common original refreshes only')
Path(sys.argv[2]).with_suffix('.capture-parity.json').write_text(json.dumps(out,indent=2));print('PASS exact sections',len(checks))
