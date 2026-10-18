"""Offline current candidate allocation census; never changes live GC policy."""
import gc,runpy,json,collections,types,contextlib,io,ctypes as C
from pathlib import Path
import owned_scenery_thread_library_install_candidate
import owned_visibility_thread_library_install_candidate
import owned_viewport_bounds_fixed_types_install_candidate
import owned_wall_record_reuse_install_candidate
import owned_record_miss_container_reuse_install_candidate
import owned_rom_slice_reuse_install_candidate
import owned_endpoint_road_planner as road_planner
from owned_endpoint_road_fixed_types_candidate import endpoint_road_span_candidates
road_planner.endpoint_road_span_candidates=endpoint_road_span_candidates
import sys
if '--reuse-library' in sys.argv:import owned_road_planner_library_install_candidate
saved=gc.get_debug();assert not gc.garbage
try:
 with contextlib.redirect_stdout(io.StringIO()):ns=runpy.run_path('work/camera/test_precomputed_decode_release_candidate.py',run_name='__main__')
 road_planner.endpoint_road_span_candidates=endpoint_road_span_candidates
 gc.collect()
 def workload():
  history=ns['EndpointRoadPlanner'](ns['rom'],ns['table']);history.scratch=ns['restore'](history.d,ns['h']['scratch']);history.epoch=ns['h']['epoch'];history.refresh=ns['h']['refresh']
  prepared=ns['Candidate'](*ns['frames'],*ns['scenes'],history,ns['roads'],ns['rom'])
  cached=None
  try:
   cached=ns['PrecomputedSourceWorldSamples'](prepared,ns['alphas'])
   for alpha,expected in zip(ns['alphas'],ns['results'][1]):
    assert ns['signature'](cached.sample(alpha))['buffers']==expected['buffers']
  finally:
   if cached is not None:cached.close()
   prepared.close();history.close()
 gc.set_debug(gc.DEBUG_SAVEALL)
 for trial in range(8):workload()
 collected=gc.collect()
 counts=collections.Counter(type(x).__module__+'.'+type(x).__qualname__ for x in gc.garbage)
 functions=collections.Counter(x.__code__.co_filename+':'+x.__qualname__ for x in gc.garbage if isinstance(x,types.FunctionType))
 libraries=collections.Counter((str(x._name),tuple(sorted(k for k,v in vars(x).items() if isinstance(v,C._CFuncPtr)))) for x in gc.garbage if isinstance(x,C.CDLL))
 arrays=collections.Counter((getattr(x,'__module__',''),getattr(x,'__name__','')) for x in gc.garbage if isinstance(x,type) and hasattr(x,'_length_'))
 out=dict(result='PASS_OFFLINE_CURRENT_CANDIDATE_CYCLE_CENSUS',collected=collected,objects=len(gc.garbage),types=counts.most_common(20),libraries=[dict(path=k[0],exports=k[1],count=n) for k,n in libraries.most_common()],functions=functions.most_common(20),array_classes=[dict(module=k[0],name=k[1],count=n) for k,n in arrays.most_common()],scope='Warm captured preparation parity workload with current record/ROM/wall reuse and configured libraries; eight actual preparation lifecycles after warm setup; setup namespace retained outside measurement, no test JSON serialization inside workload. Not live generation2 provenance or cadence proof.')
finally:
 gc.set_debug(saved);gc.garbage.clear();gc.collect()
Path('work/camera/prototype-runs/record-reuse-cycle-census-'+('library' if '--reuse-library' in sys.argv else 'baseline')+'-20261009.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
