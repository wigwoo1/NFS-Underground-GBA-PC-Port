"""Alternating complete source precompute, fresh private history per trial."""
import sys,json,time,hashlib,statistics
from pathlib import Path
prefix=Path('work/camera/test_child_road_wrapper_current_4k_candidate.py').read_text().split("if __name__=='__main__':")[0]
exec(compile(prefix,'current-precompute-imports','exec'))
import owned_motion_visibility as motion,owned_wall_region_candidates as endpoint
from owned_portal_traversal import traverse as reference
from owned_portal_point_reuse_candidate import traverse as candidate
report=json.loads(Path(sys.argv[1]).read_text());folder=Path(report['live_preparation_profiles'][0]['capture'])
setup=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0].replace("folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')",'folder=Path('+repr(str(folder))+')')
ns={};exec(compile(setup,'captured-setup','exec'),ns);ns['prepared'].close();ns['history'].close()
frames,scenes,rom,table=[ns[k] for k in ('frames','scenes','rom','table')]
from owned_endpoint_road_planner import EndpointRoadPlanner
timings=[[],[]];expected=None;checks=0
try:
 for repeat in range(8):
  for mode in ((0,1) if repeat%2==0 else (1,0)):
   motion.traverse=endpoint.traverse=(reference,candidate)[mode]
   history=EndpointRoadPlanner(rom,table);owner=None
   try:
    roads,_=history.plan(scenes[0].graph)
    start=time.perf_counter_ns()
    prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom)
    owner=PrecomputedSourceWorldSamples(prepared,(.1,.35,.9))
    timings[mode].append((time.perf_counter_ns()-start)/1e6)
    values=tuple(fingerprint(owner,a) for a in (.1,.35,.9))
    if expected is None:expected=values
    else:assert values==expected;checks+=3
   finally:
    if owner is not None:owner.close()
    history.close()
finally:motion.traverse=endpoint.traverse=reference
out=dict(result='PASS_EXACT_ALTERNATING_COMPLETE_PRECOMPUTE',exact_sample_comparisons=checks,trials_per_variant=8,reference_ms=timings[0],candidate_ms=timings[1],reference_median_ms=statistics.median(timings[0]),candidate_median_ms=statistics.median(timings[1]),scope='Same captured pair, three fractions, fresh road history each trial; constructor and complete world/source-mask precompute timed, exact bytes/arrays/details/masks/cameras. Sequential alternating same-process test, normal GC, not live scheduling or controlled global60fps proof.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out)
