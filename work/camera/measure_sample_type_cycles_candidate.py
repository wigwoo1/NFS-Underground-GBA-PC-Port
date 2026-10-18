import sys,json,gc,collections,time,statistics
from pathlib import Path
mode=sys.argv[1];source=Path('work/camera/test_prepared_world_release_candidate.py').read_text().split('results=[]')[0];exec(compile(source,'captured_setup','exec'))
from owned_prepared_world_segmented_candidate import PreparedWorldMotion as Segmented
from owned_precomputed_decode_release_candidate import PrecomputedSourceWorldSamples
import owned_endpoint_road_planner as planner_module
from owned_endpoint_road_selection_reuse_candidate import endpoint_road_span_candidates
planner_module.endpoint_road_span_candidates=endpoint_road_span_candidates
if mode=='candidate':
 from owned_sample_types_install_candidate import install
 install()
def workload():
 history=EndpointRoadPlanner(rom,table);history.scratch=restore(history.d,h['scratch']);history.epoch=h['epoch'];history.refresh=h['refresh']
 prepared=Segmented(*frames,*scenes,history,roads,rom);begin=time.perf_counter_ns();cached=PrecomputedSourceWorldSamples(prepared,alphas);elapsed=time.perf_counter_ns()-begin
 hashes=[signature(cached.sample(a))['buffers'] for a in alphas];cached.close();history.close();return elapsed,hashes
workload();gc.collect();assert not gc.garbage;enabled=gc.isenabled();debug=gc.get_debug();durations=[];hashes=[]
try:
 gc.disable();gc.set_debug(gc.DEBUG_SAVEALL)
 for i in range(8):
  elapsed,result=workload();durations.append(elapsed);hashes.append(result)
 collected=gc.collect();counts=collections.Counter(type(x).__module__+'.'+type(x).__qualname__ for x in gc.garbage)
 arrays=collections.Counter(getattr(x,'__module__','')+'.'+getattr(x,'__name__','') for x in gc.garbage if isinstance(x,type) and hasattr(x,'_length_'))
 out=dict(mode=mode,intervals=8,collected_unreachable=collected,types=counts.most_common(),array_classes=arrays.most_common(),median_precompute_ns=statistics.median(durations),timings_ns=durations,signatures=hashes,scope='Same captured8intervals, roadreuse and segmented both; GCdisabledonlyworkload thenDEBUG_SAVEALLcensus. No liveGC/cadence certification.')
finally:
 gc.set_debug(debug);gc.garbage.clear();gc.collect()
 if enabled:gc.enable()
Path('work/camera/prototype-runs/sample-types-cycle-'+mode+'-20261008.json').write_text(json.dumps(out,indent=2));print(mode,collected,out['median_precompute_ns'],sum(arrays.values()))
