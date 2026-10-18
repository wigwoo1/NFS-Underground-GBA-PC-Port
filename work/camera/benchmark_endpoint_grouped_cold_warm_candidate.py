"""Alternating complete source precompute, fresh private history per trial."""
import sys,json,time,hashlib,statistics
from pathlib import Path
prefix=Path('work/camera/test_child_road_wrapper_current_4k_candidate.py').read_text().split("if __name__=='__main__':")[0]
exec(compile(prefix,'current-precompute-imports','exec'))
import owned_motion_visibility as motion,owned_wall_region_candidates as endpoint
import owned_portal_traversal as traversal
from owned_portal_traversal import endpoint_delta as reference
from owned_endpoint_grouped_delta_candidate import endpoint_delta as candidate
report=json.loads(Path(sys.argv[1]).read_text());folder=Path(report['live_preparation_profiles'][0]['capture'])
setup=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0].replace("folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')",'folder=Path('+repr(str(folder))+')')
ns={};exec(compile(setup,'captured-setup','exec'),ns);ns['prepared'].close();ns['history'].close()
frames,scenes,rom,table=[ns[k] for k in ('frames','scenes','rom','table')]
from owned_endpoint_road_planner import EndpointRoadPlanner
import gc
import owned_endpoint_grouped_delta_candidate as grouped
rows=[];expected=None;checks=0
def cache_stats(mode):
 if mode==0:return reference.cache_info()._asdict()
 return grouped.stats()
try:
 for condition in ('cold','warm'):
  reference.cache_clear();grouped.clear()
  for repeat in range(32):
   for mode in ((0,1) if repeat%2==0 else (1,0)):
    if condition=='cold':
     reference.cache_clear();grouped.clear()
    traversal.endpoint_delta=(reference,candidate)[mode]
    before=cache_stats(mode);collections_before=[x['collections'] for x in gc.get_stats()]
    history=EndpointRoadPlanner(rom,table);owner=None
    try:
     roads,_=history.plan(scenes[0].graph)
     start=time.perf_counter_ns()
     prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom)
     owner=PrecomputedSourceWorldSamples(prepared,(.1,.35,.9))
     elapsed=(time.perf_counter_ns()-start)/1e6
     after=cache_stats(mode)
     values=tuple(fingerprint(owner,a) for a in (.1,.35,.9))
     if expected is None:expected=values
     else:assert values==expected;checks+=3
     rows.append(dict(condition=condition,repeat=repeat,variant=('reference','grouped')[mode],ms=elapsed,cache_before=before,cache_after=after,collections=[x['collections']-n for x,n in zip(gc.get_stats(),collections_before)]))
    finally:
     if owner is not None:owner.close()
     history.close()
finally:traversal.endpoint_delta=reference
summary={}
for condition in ('cold','warm'):
 summary[condition]={}
 for variant in ('reference','grouped'):
  selected=[r for r in rows if r['condition']==condition and r['variant']==variant]
  summary[condition][variant]=dict(median_ms=statistics.median(r['ms'] for r in selected),minimum_ms=min(r['ms'] for r in selected),maximum_ms=max(r['ms'] for r in selected),cache_final=selected[-1]['cache_after'],collections=[sum(r['collections'][i] for r in selected) for i in range(3)])
out=dict(result='PASS_EXACT_COLD_WARM_PRECOMPUTE',exact_sample_comparisons=checks,trials_per_condition_variant=32,summary=summary,rows=rows,scope='Same captured pair, three fractions, fresh history, normal GC. Explicit cold clears and separately retained warm caches. Collection counts include construction/fingerprint work; not exclusive cache GC cost or live cadence proof.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(dict(result=out['result'],checks=checks,summary=summary),indent=2))
