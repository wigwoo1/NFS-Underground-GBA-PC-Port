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
import owned_commit_callback_reuse_install_candidate as reuse
import sys,json,ctypes as C,weakref,time,gc,statistics
from pathlib import Path

mode=sys.argv[2];assert mode in ('private','transactional')
setup=Path('work/camera/test_owned_native_source_backdrop_batch_parity_candidate.py').read_text().split('session=None;results=[]')[0]
exec(compile(setup,'captured_private_setup','exec'))
import struct,hashlib
from owned_prepared_world_segmented_candidate import PreparedWorldMotion
from owned_source_segmented_draw_candidate import OwnedSourceDraw
from owned_native_source_segmented_release_worker_candidate import NativeSourceWorker
if mode=='transactional':
 reference_frames=[]
 for frame in frames:
  refresh=struct.unpack_from('<I',frame,4)[0]
  reference=(Path('work/camera/prototype-runs/prepared-reference-pair-20261009')/(str(refresh)+'.transactional.frame.bin')).read_bytes()
  assert frame==reference
  reference_frames.append(reference)
 frames=reference_frames
expected=[dict(alpha=.5,pair=p,variant=v) for p in range(40) for v in (('original','reused') if p%2==0 else ('reused','original'))]
prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom)
cached=PrecomputedSourceWorldSamples(prepared,(.5,))
older,newer=[scene.graph.refresh for scene in scenes]
boundaries=[]
for scene in scenes:
 record=next(x for x in report['sky_capture_records'] if (x['epoch'],x['publication'])==scene.identity)
 origin=record['asset_origin'];offset=record['source']-0x08000000
 boundaries.append(SkyBoundary(record['epoch'],record['publication'],record['angle'],240,64,0,record['source'],origin,0x06002940,rom[offset:offset+15136]))
origin=boundaries[0].asset_origin;asset=SkyAsset(origin,rom[origin-0x08000000:origin-0x08000000+15376])
worker=NativeSourceWorker();epoch=struct.unpack_from('<Q',frames[0],24)[0];rows=[]
from owned_native_source_timed_commit_adapter_candidate import NativeSourceCommitAdapter
authority=C.CDLL(str(Path("work/camera/owned-draw-commit-candidate.dll").resolve()));authority.nf_owned_handoff_create.argtypes=[C.c_uint64];authority.nf_owned_handoff_create.restype=C.c_void_p;authority.nf_owned_handoff_destroy.argtypes=[C.c_void_p]
owner=authority.nf_owned_handoff_create(epoch);assert owner
adapters={"original":reuse.Base(worker,owner),"reused":NativeSourceCommitAdapter(worker,owner)}
try:
 worker.prefetch_hud(tuple(frames),epoch,1).result(20)
 for index,item in enumerate(expected):
  alpha=item['alpha'];frame,camera,models,bounds,detail=cached.sample(alpha);offsets,mask,total,_=cached.source_masks[alpha]
  owned=OwnedSourceDraw(frame,camera,models,bounds,detail['geometry_records'],*cached.source_cameras,alpha,offsets,mask,total).attach_sky(asset.sample_continuous(*boundaries,alpha))
  authority.nf_owned_handoff_destroy(owner);owner=authority.nf_owned_handoff_create(epoch);assert owner
  adapter=adapters[item['variant']];adapter.owner=owner
  begun=time.perf_counter_ns();cpu=time.thread_time_ns()
  commit=adapter.run(owned,epoch,1,older,newer,index,alpha,0,diagnostic=True)
  elapsed=time.perf_counter_ns()-begun;cpu=time.thread_time_ns()-cpu
  assert commit['native_result']==1 and commit['commit'][:5]==[epoch,1,older,newer,index]
  row=commit['prepared']
  assert row['publication'][:3]==[epoch,1,index]
  assert commit['presentation']['status']==0
  rows.append(dict(alpha=alpha,sha256=row['native_rgb_sha256'],pair=item['pair'],variant=item['variant'],elapsed_ns=elapsed,caller_cpu_ns=cpu))
finally:worker.close();authority.nf_owned_handoff_destroy(owner);cached.close();history.close()
assert not worker.thread.is_alive() and worker.error is None
library=C.CDLL(str(Path('work/camera/owned-gpu-source-packet-profile-candidate.dll').resolve()));stats=(C.c_uint64*3)();assert library.nf_hud_owner_stats(stats)==1 and list(stats)==[0,0,0]
assert len({x['sha256'] for x in rows})==1
assert reuse.stats['calls']==40 and reuse.stats['active']==0
paired={p:{x['variant']:x for x in rows if x['pair']==p} for p in range(4,40)}
summary={metric:dict(original_median=statistics.median(x['original'][metric] for x in paired.values()),reused_median=statistics.median(x['reused'][metric] for x in paired.values()),paired_difference_median=statistics.median(x['reused'][metric]-x['original'][metric] for x in paired.values())) for metric in ['elapsed_ns','caller_cpu_ns']}
out=dict(matched_summary=summary,warmup_pairs_excluded=4,callback_activation=dict(reuse.stats),actual_native_commit=True,mode=mode,rows=rows,width=3840,height=2160,owners=list(stats),scope='Actual captured prepared-reader pair (endpointcapsules prepared synchronously in diagnostic) sampled and queued to current segmented native consumer; reference uses simultaneous transactional reader bytes. Does not prove live swap or timing fidelity.')
Path('work/camera/prototype-runs/reused-callback-matched-'+mode+'-20261009.json').write_text(json.dumps(out,indent=2));print('RENDERED',mode,len(rows))
