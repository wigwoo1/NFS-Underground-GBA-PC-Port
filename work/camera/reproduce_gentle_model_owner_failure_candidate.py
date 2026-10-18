from pathlib import Path
import sys,json,inspect,struct,traceback
sys.path.insert(0,str(Path("work/camera").resolve()))
import owned_model_record_owners as owners
captured=[]
def report(scene,visits,row,index,matches,external,owned_scene):
 captured.append(dict(refresh=scene.refresh,index=index,matches=list(matches),external=dict(external),descriptor=bytes(row["blocks"][1]).hex(),matrix=bytes(row["blocks"][2]).hex(),visits=[dict(object=v["object"],dispatch=v["dispatch"],source=bytes(v["source"]).hex()) for v in visits]))
source=inspect.getsource(owners.endpoint_model_record_owners)
needle="if len(matches)!=1:raise ValueError('Ambiguous or missing source model record owner')"
assert source.count(needle)==1
source=source.replace(needle,"if len(matches)!=1:report(scene,visits,row,index,matches,external,owned_scene);raise ValueError('Ambiguous or missing source model record owner')")
ns=dict(owners.endpoint_model_record_owners.__globals__,report=report)
exec(compile(source,"model-owner-diagnostic","exec"),ns)
owners.endpoint_model_record_owners=ns["endpoint_model_record_owners"]
folder=Path("work/camera/prototype-runs/fullscene-failure-1791575541143887200")
setup=Path("work/camera/test_external_changed_parent_exit.py").read_text().split("gpu=C.CDLL")[0]
setup=setup.replace("folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')","folder=Path("+repr(str(folder))+")")
setup=setup.replace("from owned_prepared_world_motion import PreparedWorldMotion","from owned_prepared_world_segmented_candidate import PreparedWorldMotion")
env={}
error=None
try:
 exec(compile(setup,"captured-model-failure-setup","exec"),env)
 from owned_precomputed_decode_release_candidate import PrecomputedSourceWorldSamples
 samples=PrecomputedSourceWorldSamples(env["prepared"],(.2,.5,.8))
 samples.close()
except BaseException as e:error=repr(e);detail=traceback.format_exc()
finally:
 for name in ("prepared","history"):
  obj=env.get(name)
  if obj is not None:obj.close()
out=dict(result="REPRODUCED" if captured else "NOT_REPRODUCED",error=error,owners=captured,traceback=detail if error else None)
Path("outputs/nfsug-native-renderer/camera-research/gentle-model-owner-reproduction-20261009.json").write_text(json.dumps(out,indent=2))
print(out["result"],error)
for row in captured:print("row",row["index"],"refresh",row["refresh"],"matches",row["matches"],"visits",[(v["object"],v["dispatch"]) for v in row["visits"]])
