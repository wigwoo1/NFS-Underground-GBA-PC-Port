"""Offscreen captured replay heap census; normal GC policy unchanged."""
import gc,json,sys,time,collections
from pathlib import Path
import test_request_release_process_4k_candidate
import owned_rom_slice_reuse_install_candidate
import owned_record_miss_container_reuse_install_candidate
import owned_road_planner_library_install_candidate
import owned_road_material_decode_install_candidate
import owned_extent_sidecar_encode_install_candidate
from owned_precomputed_decode_release_candidate import PrecomputedSourceWorldSamples
from owned_prepared_world_segmented_candidate import PreparedWorldMotion
from owned_endpoint_road_planner import EndpointRoadPlanner
from owned_gc_trace import CollectionTrace
if '--fixed-types' in sys.argv:import owned_preparation_fixed_types_install_candidate
report=json.loads(Path(sys.argv[1]).read_text());folder=Path(report['live_preparation_profiles'][0]['capture'])
source=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0].replace("folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')",'folder=Path('+repr(str(folder))+')')
ns={};exec(compile(source,'heap-captured-fixture','exec'),ns);ns['prepared'].close();ns['history'].close()
frames,scenes,rom,table=[ns[k] for k in ('frames','scenes','rom','table')]
policy=(gc.isenabled(),gc.get_threshold());assert policy[0]
def census():
 objects=gc.get_objects();counts=collections.Counter(type(x).__module__+'.'+type(x).__qualname__ for x in objects);total=len(objects);del objects
 return dict(total=total,types=dict(counts))
baseline=census();snapshots=[];trace=CollectionTrace();durations=[]
try:
 for i in range(24):
  started=time.perf_counter_ns();history=EndpointRoadPlanner(rom,table);roads,_=history.plan(scenes[0].graph);prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom);samples=PrecomputedSourceWorldSamples(prepared,(.1,.35,.9),trace=True)
  if i in (0,7,23):snapshots.append(dict(iteration=i,phase='samples_alive',**census()))
  samples.close();history.close();del samples,prepared,history,roads
  durations.append((time.perf_counter_ns()-started)/1e6)
  if i in (0,7,23):snapshots.append(dict(iteration=i,phase='closed',**census()))
finally:trace.close()
assert policy==(gc.isenabled(),gc.get_threshold())
final=snapshots[-1];delta=sorted(((k,v-baseline['types'].get(k,0)) for k,v in final['types'].items()),key=lambda x:x[1],reverse=True)
out=dict(result='DIAGNOSTIC_NORMAL_GC_PREPARATION_HEAP_CENSUS',baseline=baseline,snapshots=snapshots,largest_closed_type_increases=delta[:30],durations_ms=durations,gc_events=trace.rows,gc_dropped=trace.dropped,gc_policy_unchanged=True,scope='24 cold captured preparation lifecycles, offscreen component diagnostic. Census allocates temporary references; not live cadence or exclusive retention-leak proof.')
Path('work/camera/prototype-runs/'+('preparation-heap-fixed-saveall-20261009.json' if '--fixed-types' in sys.argv and gc.get_debug() & gc.DEBUG_SAVEALL else 'preparation-heap-fixed-20261009.json' if '--fixed-types' in sys.argv else 'preparation-heap-saveall-20261009.json' if gc.get_debug() & gc.DEBUG_SAVEALL else 'preparation-heap-20261009.json')).write_text(json.dumps(out,indent=2));print(json.dumps(dict(baseline_total=baseline['total'],final_total=final['total'],largest_closed_type_increases=delta[:15],gc_events=len(trace.rows)),indent=2))
