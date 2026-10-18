"""Controlled saved-source preparation; excludes gameplay and image rendering."""
from pathlib import Path
import sys,time,json,hashlib,statistics
sys.path.insert(0,str(Path("work/camera").resolve()))
from owned_endpoint_road_planner import EndpointRoadPlanner
from owned_prepared_world_segmented_candidate import PreparedWorldMotion
from owned_precomputed_decode_release_candidate import PrecomputedSourceWorldSamples
setup=Path("work/camera/test_external_changed_parent_exit.py").read_text().split("gpu=C.CDLL")[0].replace("1791308040881565000","1791576492416199100").replace("from owned_prepared_world_motion import PreparedWorldMotion","from owned_prepared_world_segmented_candidate import PreparedWorldMotion")
env={};exec(setup,env);env["prepared"].close();env["history"].close()
import owned_source_model_anchor_candidate as anchors
import owned_source_face_mask_candidate as masks
from owned_motion_pairs import records as original_records
from owned_model_key_records_candidate import records as model_records
alphas=(.125,.375,.625,.875);rows=[];reference=None
for iteration in range(32):
 anchors.records=masks.records=model_records if iteration%2 else original_records
 begin=time.perf_counter_ns();cpu=time.thread_time_ns()
 history=EndpointRoadPlanner(env["rom"],env["table"]);samples=None;prepared=None
 try:
  roads,_=history.plan(env["scenes"][0].graph)
  prepared=PreparedWorldMotion(*env["frames"],*env["scenes"],history,roads,env["rom"])
  samples=PrecomputedSourceWorldSamples(prepared,alphas,trace=False)
  elapsed=time.perf_counter_ns()-begin;executed=time.thread_time_ns()-cpu
  # Hash after timing, so evidence checking is outside measured workload.
  fingerprint=[hashlib.sha256(bytes(samples.sample(a)[0])+b''.join(bytes(v) for v in samples.sample(a)[1:4])+b''.join(bytes(v) for v in samples.source_masks[a][:2])).hexdigest() for a in alphas]
  if reference is None:reference=fingerprint
  assert fingerprint==reference
  rows.append(dict(iteration=iteration,model_only_keys=bool(iteration%2),wall_ms=elapsed/1e6,cpu_ms=executed/1e6,bytes=samples.bytes))
 finally:
  if samples is not None:samples.close()
  if prepared is not None:prepared.close()
  history.close()
out=dict(result="PASS_CONTROLLED_SOURCE_PREPARATION",iterations=32,samples_per_iteration=4,
 source_capture="fullscene-failure-1791576492416199100",source_frame_hashes=reference,rows=rows,
 warm_wall_mean_ms=statistics.mean(x["wall_ms"] for x in rows[1:]),warm_cpu_mean_ms=statistics.mean(x["cpu_ms"] for x in rows[1:]),
 scope="Direct saved-source full initialization and four sampled frames, render excluded; CPU accounting quantized, warm library/cache effects included. Not representative live throughput, original clock or smooth60 proof.")
Path("outputs/nfsug-native-renderer/camera-research/model-only-keys-comparison-20261009.json").write_text(json.dumps(out,indent=2))
for enabled in (False,True):
 selected=[x for x in rows[2:] if x["model_only_keys"]==enabled]
 print("model_only_keys",enabled,"count",len(selected),"wall",statistics.mean(x["wall_ms"] for x in selected),"CPU",statistics.mean(x["cpu_ms"] for x in selected))

