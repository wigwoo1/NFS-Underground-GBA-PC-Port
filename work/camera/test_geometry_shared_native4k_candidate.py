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
import owned_ordered_render_tail_install_candidate
import owned_source_packet_phase_profile_install_candidate
import sys,json,ctypes as C,weakref
from pathlib import Path


import runpy,hashlib
import owned_wall_record_reuse_install_candidate
from owned_child_road_wrapper_reuse_process_candidate import ProcessPreparationService
from owned_precomputed_decode_release_candidate import PrecomputedSourceWorldSamples
from owned_prepared_world_segmented_candidate import PreparedWorldMotion

def fingerprint(owner,alpha):
 v=owner.sample(alpha);m=owner.source_masks[alpha]
 return (bytes(v[0]),*(None if x is None else bytes(x) for x in v[1:4]),v[4],bytes(m[0]),bytes(m[1]),m[2],m[3],owner.source_cameras)
import owned_native_transaction_worker_install_candidate
import owned_sky_linear_backend_install_candidate
import time
import owned_hud_short_lock_renderer_install_candidate
if __name__=='__main__':
 import owned_source_presentation_batch_candidate as batch
 from owned_source_depth_transition_candidate import SourceFaceDeterminants
 batch.SourceFaceDeterminants=SourceFaceDeterminants
 report=json.loads(Path(sys.argv[1]).read_text());folder=Path(report['live_preparation_profiles'][0]['capture'])
 provenance=dict(capture=str(folder),files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.iterdir() if p.is_file()},sky_records=report['sky_capture_records'])
 source=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0].replace("folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')",'folder=Path('+repr(str(folder))+')')
 ns={};exec(compile(source,'captured_process_setup','exec'),ns);ns['prepared'].close();ns['history'].close()
 frames,scenes,rom,table=[ns[k] for k in ('frames','scenes','rom','table')]
 from owned_endpoint_road_planner import EndpointRoadPlanner
 history=EndpointRoadPlanner(rom,table);roads,_=history.plan(scenes[0].graph);prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom)
 alphas=(.01,.2,.4,.6,.8,.99);direct=PrecomputedSourceWorldSamples(prepared,alphas);expected={a:fingerprint(direct,a) for a in alphas}

 from owned_sky_boundary import SkyBoundary
 from owned_sky_sampler import SkyAsset
 from owned_source_segmented_draw_candidate import OwnedSourceDraw
 from owned_native_source_segmented_release_worker_candidate import NativeSourceWorker
 boundaries=[]
 for scene in scenes:
  record=next(x for x in report['sky_capture_records'] if (x['epoch'],x['publication'])==scene.identity)
  origin=record['asset_origin'];offset=record['source']-0x08000000
  boundaries.append(SkyBoundary(record['epoch'],record['publication'],record['angle'],240,64,0,record['source'],origin,0x06002940,rom[offset:offset+15136]))
 origin=boundaries[0].asset_origin;asset=SkyAsset(origin,rom[origin-0x08000000:origin-0x08000000+15376])
 gpu=NativeSourceWorker();epoch=scenes[0].graph.epoch;gpu.prefetch_hud(tuple(frames),epoch,1).result(20)
 rows=[];rendered=[]
 authority=C.CDLL(str((Path(__file__).parent/'owned-draw-commit-highres-candidate.dll').resolve()));authority.nf_owned_handoff_create.argtypes=[C.c_uint64];authority.nf_owned_handoff_create.restype=C.c_void_p;authority.nf_owned_handoff_destroy.argtypes=[C.c_void_p]
 native_owner=authority.nf_owned_handoff_create(epoch);assert native_owner
 native_function=C.cast(authority.nf_owned_handoff_draw_wait_commit_sample,C.c_void_p)
 import multiprocessing as mp
 from owned_progressive_fixture_process_candidate import worker
 def render(value,packed,cameras,alpha):
  frame,camera,models,bounds,detail=value;offsets,mask,total,_=packed
  owned=OwnedSourceDraw(frame,camera,models,bounds,detail['geometry_records'],*cameras,alpha,offsets,mask,total).attach_sky(asset.sample_continuous(*boundaries,alpha))
  index=len(rendered);row=gpu.prepare(owned,epoch,1,index,True).result(20)
  assert row['publication'][:3]==[epoch,1,index]
  deadline=time.perf_counter_ns()+2_000_000
  tx=gpu.commit_present(native_function,native_owner,epoch,1,scenes[0].identity[1],scenes[1].identity[1],index,alpha,deadline).result(20)
  assert tx['native_result']==1 and tx['native_callback_count']==1 and tx['native_batch_result']==0
  assert tx['commit'][:5]==[epoch,1,scenes[0].identity[1],scenes[1].identity[1],index]
  assert tx['wait'][1]==deadline and tx['wait'][2]>=deadline and tx['commit'][6]>=deadline
  assert tx['renderer_dispatch']['thread']==gpu.thread.ident and tx['presentation']['status']==0
  rendered.append(dict(index=index,alpha=alpha,sha256=row['native_rgb_sha256']))
  return row['native_rgb_sha256']
 from owned_geometry_preparation_adapter_candidate import ProgressivePreparationAdapter
 service=ProgressivePreparationAdapter(rom,shared_output=True)
 try:
  for generation in (0,1):
   reference=[render(direct.sample(a),direct.source_masks[a],direct.source_cameras,a) for a in alphas]
   if generation:service.invalidate()
   future=service.submit(*list(zip(frames,scenes)),alphas,timeout=5);pair=service.take(future);received=[]
   try:
    for a in alphas:
     assert fingerprint(pair,a)==expected[a]
     received.append(render(pair.sample(a),pair.source_masks[a],pair.source_cameras,a))
    assert received==reference
    rows.append(dict(generation=generation,exact_source_samples=True,exact_native_4k=True,worker_pid=service.service.process.pid))
   finally:pair.close()
 finally:
  service.close();gpu.close();authority.nf_owned_handoff_destroy(native_owner);direct.close();history.close()
 assert not service.thread.is_alive() and not service.service.process.is_alive() and not service.errors,service.errors
 assert not gpu.thread.is_alive() and gpu.error is None
 library=C.CDLL(str(Path('work/camera/owned-gpu-source-packet-short-lock-candidate.dll').resolve()));stats=(C.c_uint64*3)();assert library.nf_hud_owner_stats(stats)==1 and list(stats)==[0,0,0]
 out=dict(result='PASS_GEOMETRY_SHARED_ADAPTER_NATIVE_4K',native_4k_readbacks=len(rendered),rows=rows,rendered=rendered,fixture_provenance=provenance,scope='Saved-fixture actual 4K source draw and native commit. First-ready Future/per-alpha waits feed native renderer while adapter copies and acknowledges samples independently. Same persistent worker across completed-request generation reset; not live pause during native draw, live gameplay timing or original fullscene fidelity/scanout proof.')
 Path('outputs/nfsug-native-renderer/camera-research/checkpoints/all-successful-native-starvation-20261010/geometry-shared-native4k.json').write_text(json.dumps(out,indent=2));print(out['result'],len(rendered))
