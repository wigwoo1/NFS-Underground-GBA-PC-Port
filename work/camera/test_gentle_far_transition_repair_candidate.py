from pathlib import Path
import sys,json,inspect
sys.path.insert(0,str(Path("work/camera").resolve()))
setup=Path("work/camera/test_external_changed_parent_exit.py").read_text().split("gpu=C.CDLL")[0].replace("1791308040881565000","1791576492416199100").replace("from owned_prepared_world_motion import PreparedWorldMotion","from owned_prepared_world_segmented_candidate import PreparedWorldMotion")
env={};exec(setup,env)
try:
 from owned_model_record_owners import model_record_owners
 from owned_sampled_model_visit import sampled_model_visit
 pair=env["prepared"].pair;maps=model_record_owners(pair,env["rom"])
 assert 34 in maps[0].values() and 34 not in maps[1].values()
 assert pair._scenery_far_exit=={34}
 original=inspect.getsource(sampled_model_visit)
 needle=" if depth>=8192:\n  if object_index in getattr(pair,'_scenery_far_exit',set()):return None\n  raise ValueError('Unverified ordinary far-depth transition')\n"
 assert original.count(needle)==1
 ns=dict(sampled_model_visit.__globals__);exec(original.replace(needle,""),ns)
 rows=[]
 for i in range(1,100):
  alpha=i/100;reference=ns["sampled_model_visit"](pair,alpha,34);actual=sampled_model_visit(pair,alpha,34)
  assert (actual is None)==(reference["depth"]>=8192)
  if actual is not None:assert actual==reference
  env["prepared"].sample(alpha)
  rows.append(dict(alpha=alpha,depth=reference["depth"],visible=actual is not None))
 assert any(r["visible"] for r in rows) and any(not r["visible"] for r in rows)
 assert env["prepared"].sample(0)[0]==env["frames"][0] and env["prepared"].sample(1)[0]==env["frames"][1]
 from owned_model_record_builder import ModelRecordBuilder
 from owned_ordinary_model_visits import ordinary_model_visits
 builder=ModelRecordBuilder(env["rom"]);near=next(v for v in ordinary_model_visits(env["scenes"][0].graph,pair.portal.sample(0)) if v["object"]==34)
 rejected=0
 for visit in (near,dict(near,depth=8192)):
  try:builder.prepare_far_hidden(env["scenes"][0],pair.portal.sample(0),visit)
  except ValueError:rejected+=1
 assert rejected==2
 from owned_precomputed_decode_release_candidate import PrecomputedSourceWorldSamples
 samples=PrecomputedSourceWorldSamples(env["prepared"],(.2,.5,.8));samples.close()
 result=dict(result="PASS",owner=34,source_endpoints_exact=2,samples=rows,negative_checks=rejected,precomputed_samples=3,scope="Savedfar crossing with original threshold; exact source endpoints, nonculled visits unchanged and private asset guards. No live cadence/fullscene raster equivalence.")
 Path("outputs/nfsug-native-renderer/camera-research/gentle-far-transition-repair-20261009.json").write_text(json.dumps(result,indent=2));print("PASS",len(rows),"samples",rejected,"rejections")
finally:env["prepared"].close();env["history"].close()
