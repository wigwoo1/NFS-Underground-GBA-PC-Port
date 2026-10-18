from pathlib import Path
import sys,json,traceback
sys.path.insert(0,str(Path("work/camera").resolve()))
from owned_model_record_builder import ModelRecordBuilder
original=ModelRecordBuilder._prepare;failures=[]
def diagnostic(self,scene,queue,visit,*args,**kwargs):
 try:return original(self,scene,queue,visit,*args,**kwargs)
 except BaseException:
  failures.append(dict(refresh=scene.graph.refresh,source_refresh=scene.graph.graph.refresh,visit=dict(visit,source=bytes(visit["source"]).hex()),args=args,kwargs=kwargs))
  raise
ModelRecordBuilder._prepare=diagnostic
setup=Path("work/camera/test_external_changed_parent_exit.py").read_text().split("gpu=C.CDLL")[0].replace("1791308040881565000","1791576492416199100").replace("from owned_prepared_world_motion import PreparedWorldMotion","from owned_prepared_world_segmented_candidate import PreparedWorldMotion")
env={};error=None
try:
 exec(setup,env)
 from owned_precomputed_decode_release_candidate import PrecomputedSourceWorldSamples
 samples=PrecomputedSourceWorldSamples(env["prepared"],(.2,.5,.8));samples.close()
except BaseException as e:error=repr(e);detail=traceback.format_exc()
finally:
 for key in ("prepared","history"):
  if env.get(key) is not None:env[key].close()
out=dict(result="REPRODUCED" if failures else "NOT_REPRODUCED",error=error,failures=failures,traceback=detail if error else None)
Path("outputs/nfsug-native-renderer/camera-research/gentle-material-failure-20261009.json").write_text(json.dumps(out,indent=2))
print(out["result"],error)
for f in failures:print(f["refresh"],f["visit"]["object"],f["visit"]["bounds"],f["visit"]["dispatch"],f["args"])
