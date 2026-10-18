import json,traceback
from pathlib import Path
p=Path('work/camera/test_external_changed_parent_exit.py');source=p.read_text().split('gpu=C.CDLL')[0].replace("folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')","folder=Path('work/camera/prototype-runs/fullscene-failure-1791505088433840800')");ns={};out={}
try:
 exec(compile(source,'failure_scene_setup','exec'),ns)
 from owned_precomputed_source_samples_candidate import PrecomputedSourceWorldSamples
 cached=PrecomputedSourceWorldSamples(ns['prepared'],(.2,.4,.6,.8),trace=True);cached.close();out['result']='NOT_REPRODUCED'
except Exception as e:out.update(result='REPRODUCED_SOURCE_PREPARATION_FAILURE',error=repr(e),traceback=traceback.format_exc())
finally:
 for k in ('prepared','history'):
  if ns.get(k):ns[k].close()
out['scope']='Captured complete scene pair source preparation only, no backdrop renderer or GPU session created.'
Path('work/camera/prototype-runs/native-projection-failure-replay-20261008.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
