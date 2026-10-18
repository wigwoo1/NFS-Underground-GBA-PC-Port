import owned_scenery_thread_library_install_candidate
import owned_endpoint_road_planner as road_planner
from owned_endpoint_road_fixed_types_candidate import endpoint_road_span_candidates
road_planner.endpoint_road_span_candidates=endpoint_road_span_candidates
import owned_viewport_bounds_fixed_types_install_candidate
import owned_visibility_thread_library_install_candidate
import owned_segmented_display_placement_install_candidate
import owned_hud_cache_lease_worker_install_candidate
import owned_renderer_dispatch_trace_install_candidate
import owned_present_stage_trace_install_candidate
import owned_renderer_fixed_types_install_candidate
import owned_hud_prefetch_d3d_profile_install_candidate
import owned_packet_profile_install_candidate
import owned_d3d_call_profile_install_candidate
import sys,json,ctypes as C,weakref
from pathlib import Path


import gc,time,struct,weakref,json
from owned_precomputed_decode_release_candidate import PrecomputedSourceWorldSamples
from owned_prepared_world_segmented_candidate import PreparedWorldMotion
from owned_road_history_diagnostic import restore
from owned_road_record_diagnostic import decode
root=Path('work/camera/prototype-runs');folders=sorted(d for d in root.iterdir() if d.is_dir() and (d/'road-history.json').exists() and (d/'prepared-signatures.json').exists());assert len(folders)<=64
source=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0]
results=[]
for folder in folders:
 ns={};history=None;prepared=None;cached=None;row=dict(folder=str(folder),result='FAILED')
 try:
  code=source.replace("folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')",'folder=Path('+repr(str(folder))+')')
  exec(compile(code,'captured_interval_setup','exec'),ns)
  ns['prepared'].close();ns['history'].close();del ns['prepared']
  frames,scenes,rom,table=[ns[k] for k in ('frames','scenes','rom','table')]
  h=json.loads((folder/'road-history.json').read_text());roads=decode(json.loads((folder/'older-roads.json').read_text()))
  history=ns['EndpointRoadPlanner'](rom,table);history.scratch=restore(history.d,h['scratch']);history.epoch=h['epoch'];history.refresh=h['refresh']
  prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom);ref=weakref.ref(prepared);pair_ref=weakref.ref(prepared.pair)
  before=len(gc.get_objects());begun=time.perf_counter_ns();cached=PrecomputedSourceWorldSamples(prepared,(.01,.5,.99));elapsed=time.perf_counter_ns()-begun
  row.update(result='PASS',older=scenes[0].graph.refresh,newer=scenes[1].graph.refresh,epoch=scenes[0].graph.epoch,sample_owned_bytes=cached.bytes,prepare_ns=elapsed,tracked_after_precompute=len(gc.get_objects()),tracked_before=before)
  cached.close();prepared.close();del cached,prepared;cached=prepared=None
  row['closed_wrapper_released']=ref() is None;row['closed_pair_released']=pair_ref() is None;assert ref() is None and pair_ref() is None
 except Exception as e:row.update(result='FAILED',error=repr(e))
 finally:
  if cached is not None:cached.close()
  if prepared is not None:prepared.close()
  if history is not None:history.close()
  for name in ('prepared','history'):
   if ns.get(name) is not None:ns[name].close()
  ns.clear()
 results.append(row)
 print(row['folder'].split('/')[-1],row['result'],row.get('error',''))
out=dict(result='CAPTURED_INTERVAL_RELEASE_COVERAGE',total=len(results),passed=sum(x['result']=='PASS' for x in results),rows=results,scope='Distinct saved endpoint pairs from existing profile capture folders; three interior samples each, authoritative precompute and segmented world, weak wrapper/pair release. Source sets may overlap and older captures may lack current snapshot dependencies. Offline only, no live cadence or image/fidelity equivalence claim.')
Path('work/camera/prototype-runs/distinct-source-release-20261009.json').write_text(json.dumps(out,indent=2));print('COVERAGE',out['passed'],out['total'])
