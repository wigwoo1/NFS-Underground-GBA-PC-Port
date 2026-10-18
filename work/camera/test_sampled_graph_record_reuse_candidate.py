import sys,json,time,statistics
from pathlib import Path
import owned_scenery_thread_library_install_candidate
import owned_visibility_thread_library_install_candidate
import owned_viewport_bounds_fixed_types_install_candidate
from owned_endpoint_road_fixed_types_candidate import endpoint_road_span_candidates
import owned_endpoint_road_planner as planner
planner.endpoint_road_span_candidates=endpoint_road_span_candidates
report=json.loads(Path(sys.argv[1]).read_text());folder=Path(report['live_preparation_profiles'][0]['capture'])
source=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0].replace("folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')",'folder=Path('+repr(str(folder))+')')
ns={};exec(compile(source,'captured_setup','exec'),ns)
import owned_wall_record_reuse_install_candidate
from owned_sampled_graph_gpu import sampled_graph_gpu_records as original
from owned_sampled_graph_record_reuse_candidate import sampled_graph_gpu_records as candidate
portal=ns['prepared'].pair.portal;timings={'original':[],'candidate':[]};checks=0
try:
 for i in range(20):
  for alpha in (0,.1,.35,.5,.9,1):
   values={}
   for name,fn in (('original',original),('candidate',candidate)) if i%2==0 else (('candidate',candidate),('original',original)):
    begin=time.perf_counter_ns();values[name]=fn(portal,alpha);timings[name].append(time.perf_counter_ns()-begin)
   assert values['original']==values['candidate'];checks+=1
 cache=portal._complete_wall_record_cache;assert cache.bytes<=8*1024*1024 and len(cache.records)<=256
 out=dict(result='PASS_CAPTURED_WALL_RECORD_REUSE',checks=checks,median_ms={k:statistics.median(v)/1e6 for k,v in timings.items()},hits=cache.hits,misses=cache.misses,retained_record_bytes=cache.bytes,scope='Same captured portal, alternating endpoint/intermediate exact records/bounds/order; excludes full renderer/live cadence.')
finally:
 from owned_wall_record_reuse_install_candidate import clear_closed_wall_records
 clear_closed_wall_records(ns['prepared']);ns['prepared'].close();ns['history'].close()
 assert portal._complete_wall_record_cache.bytes==0 and not portal._complete_wall_record_cache.records
 out['closed_retained_portal_cache_empty']=True
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out)
