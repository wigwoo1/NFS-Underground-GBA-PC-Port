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
from owned_material_decode_process_service_candidate import ProcessPreparationService
from owned_precomputed_decode_release_candidate import PrecomputedSourceWorldSamples
from owned_prepared_world_segmented_candidate import PreparedWorldMotion

def fingerprint(owner,alpha):
 v=owner.sample(alpha);m=owner.source_masks[alpha]
 return (bytes(v[0]),*(None if x is None else bytes(x) for x in v[1:4]),v[4],bytes(m[0]),bytes(m[1]),m[2],m[3],owner.source_cameras)
import owned_hud_sky_capture_backend_install_candidate
if __name__=='__main__':
 report=json.loads(Path(sys.argv[1]).read_text());folder=Path(report['live_preparation_profiles'][0]['capture'])
 provenance=dict(capture=str(folder),files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.iterdir() if p.is_file()},sky_records=report['sky_capture_records'])
 source=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0].replace("folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')",'folder=Path('+repr(str(folder))+')')
 ns={};exec(compile(source,'captured_process_setup','exec'),ns);ns['prepared'].close();ns['history'].close()
 frames,scenes,rom,table=[ns[k] for k in ('frames','scenes','rom','table')]
 from owned_endpoint_road_planner import EndpointRoadPlanner
 history=EndpointRoadPlanner(rom,table);roads,_=history.plan(scenes[0].graph);prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom)
 alphas=(.1,.35,.9);direct=PrecomputedSourceWorldSamples(prepared,alphas);expected={a:fingerprint(direct,a) for a in alphas};service=ProcessPreparationService(rom,2)

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
 try:
  for iteration in range(2):
   if iteration:service.invalidate()
   received=service.take(service.submit(*list(zip(frames,scenes)),alphas,timeout=5))
   try:
    assert all(fingerprint(received,a)==expected[a] for a in alphas)
    assert received.endpoint_base_reuses==len(alphas)

    hashes={}
    for variant,owner in [('direct',direct),('process',received)]:
     hashes[variant]=[]
     for alpha in alphas:
      frame,camera,models,bounds,detail=owner.sample(alpha);offsets,mask,total,_=owner.source_masks[alpha]
      owned=OwnedSourceDraw(frame,camera,models,bounds,detail['geometry_records'],*owner.source_cameras,alpha,offsets,mask,total).attach_sky(asset.sample_continuous(*boundaries,alpha))
      index=len(rendered);row=gpu.prepare(owned,epoch,1,index,True).result(20)
      assert row['publication'][:3]==[epoch,1,index]
      assert gpu.present(epoch,1,index).result(20)['status']==0
      hashes[variant].append(row['native_rgb_sha256']);rendered.append(dict(iteration=iteration,variant=variant,alpha=alpha,index=index,sha256=row['native_rgb_sha256']))
    assert hashes['direct']==hashes['process']
    rows.append(dict(iteration=iteration,alphas=list(alphas),exact_source_samples=True,exact_native_4k=True))
   finally:received.close();assert not received.samples and not received.source_masks and not received.source_cameras
 finally:gpu.close();direct.close();service.close();history.close()
 assert service.request_owner.closed and service.shutdown_evidence['request_mapping_closed'] is True
 assert service.shared_owner.closed and service.shutdown_evidence['shared_mapping_closed'] is True
 assert not service.process.is_alive() and not gpu.thread.is_alive() and gpu.error is None
 library=C.CDLL(str(Path('work/camera/owned-gpu-source-packet-profile-candidate.dll').resolve()));stats=(C.c_uint64*3)();assert library.nf_hud_owner_stats(stats)==1 and list(stats)==[0,0,0]
 out=dict(fixture_provenance=provenance,result='PASS_SPAWNED_SEGMENTED_NATIVE_4K_PARITY',native_4k_readbacks=len(rendered),rendered=rendered,rows=rows,child_pid=service.process.pid,clean_shutdown=True,scope='Actual spawned current segmented child versus direct current thread reconstruction from same captured cold endpoint history; exact frames/arrays/details/masks/cameras, generation reset and close. Parent retains segmented immutable bytes copied before acknowledgement. Twelve actual 3840x2160 readbacks including continuous sky match direct versus spawned preparation across reset. No live game timing, original scene fidelity or scanout claim.')
 baseline=json.loads(Path('work/camera/prototype-runs/hud-target-reuse-current-check-20261009.json').read_text())
 assert provenance==baseline['fixture_provenance'], 'Different fixture/reference provenance'
 assert rendered==baseline['rendered'], 'Profiler differs from current original backend'
 Path('work/camera/prototype-runs/hud-sky-capture-off-4k-20261009.json').write_text(json.dumps(out,indent=2));print(out['result'])
