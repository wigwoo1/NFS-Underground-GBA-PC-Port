import json
from pathlib import Path
source=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0].replace("folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')","folder=Path('work/camera/prototype-runs/fullscene-failure-1791505088433840800')");ns={};results=[]
try:
 exec(compile(source,'capture_setup','exec'),ns)
 from owned_motion_pairs import records
 key=json.loads(Path('work/camera/prototype-runs/native-rejected-depth-20261008.json').read_text())['models'][0]['key']
 for i in (0,1):
  original=records(ns['frames'][i])['records'];sampled=records(ns['prepared'].sample(i)[0])['records']
  def matched(rows):return [dict(key=list(x['key']),matrix_bytes=len(x['blocks'][2]),faces=len(x['blocks'][5])) for x in rows if x['kind']==3 and list(x['key'])==key]
  results.append(dict(endpoint=i,identity=list(ns['scenes'][i].identity),captured_original_matches=matched(original),complete_world_endpoint_matches=matched(sampled)))
finally:
 for name in ('prepared','history'):
  if ns.get(name):ns[name].close()
out=dict(result='CAPTURED_REJECTED_MODEL_PRESENCE',endpoints=results,scope='Original captured draw record presence vs complete-world endpoint. Records may precede projection reject; presence is not proof pixels were emitted.')
Path('work/camera/prototype-runs/native-rejected-model-presence-20261008.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
