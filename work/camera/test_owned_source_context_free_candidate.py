import sys,json,time,threading
from pathlib import Path
from owned_road_record_diagnostic import decode
from owned_road_history_diagnostic import restore,snapshot
from owned_sample_signature import signature
report=json.loads(Path(sys.argv[1]).read_text());meta=report['live_preparation_profiles'][0];folder=Path(meta['capture'])
source=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0].replace("folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')",'folder=Path('+repr(str(folder))+')')
exec(compile(source,'captured_scene_setup','exec'));prepared.close();history.close()
h=json.loads((folder/'road-history.json').read_text());roads=decode(json.loads((folder/'older-roads.json').read_text()));expected=json.loads((folder/'prepared-signatures.json').read_text())

import ctypes as C,hashlib
from owned_precomputed_source_samples_candidate import PrecomputedSourceWorldSamples
from owned_source_draw_context_candidate import OwnedSourceDraw
from owned_sky_boundary import SkyBoundary
from owned_sky_sampler import SkyAsset
history=EndpointRoadPlanner(rom,table);history.scratch=restore(history.d,h['scratch']);history.epoch=h['epoch'];history.refresh=h['refresh'];prepared=None;cached=None
p=Path('work/camera');gpu=C.CDLL(str((p/'owned-gpu-source-context-free-candidate.dll').resolve()))
gpu.nf_owned_gpu_source_context_callback.argtypes=[C.c_void_p];gpu.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t]
present_results=[];consumer=None;consumer_stats=None;packet_checks=[];checks=[];images=[];gpu.nf_source_packets_stats.argtypes=[C.c_void_p];gpu.nf_source_packets_copy.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t]
try:
 prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom);cached=PrecomputedSourceWorldSamples(prepared,tuple(x['alpha'] for x in expected),trace=True)
 boundaries=[]
 for scene in scenes:
  record=next(x for x in report['sky_capture_records'] if (x['epoch'],x['publication'])==scene.identity)
  origin=record['asset_origin'];offset=record['source']-0x08000000
  boundaries.append(SkyBoundary(record['epoch'],record['publication'],record['angle'],240,64,0,record['source'],origin,0x06002940,rom[offset:offset+15136]))
 origin=boundaries[0].asset_origin;asset=SkyAsset(origin,rom[origin-0x08000000:origin-0x08000000+15376])
 from owned_source_d3d_present_consumer_candidate import OwnedD3DConsumer
 consumer=OwnedD3DConsumer();consumer.bind_window();gpu.nf_source_initialize.argtypes=[C.c_void_p];assert gpu.nf_source_initialize(consumer.window)==0;assert gpu.nf_owned_gpu_active_contexts()==0
 for index,item in enumerate(expected):
  gpu.nf_source_packets_begin.argtypes=[C.c_uint64]*3;gpu.nf_source_packets_identity.argtypes=[C.c_void_p]
  assert gpu.nf_source_packets_close()==0;assert gpu.nf_source_packets_begin(1,1,index)==0;assert gpu.nf_source_packets_begin(1,1,index)==1
  identity=(C.c_uint64*3)();assert gpu.nf_source_packets_identity(identity)==0 and list(identity)==[1,1,index]
  alpha=item['alpha'];frame,camera,models,bounds,detail=cached.sample(alpha);offsets,mask,total,_=cached.source_masks[alpha]
  owned=OwnedSourceDraw(frame,camera,models,bounds,detail['geometry_records'],*cached.source_cameras,alpha,offsets,mask,total).attach_sky(asset.sample_continuous(*boundaries,alpha))
  status=gpu.nf_owned_gpu_source_context_callback(C.byref(owned.context));assert status==0,status
  gpu.nf_source_packets_publish.argtypes=[C.c_void_p];publication=(C.c_uint64*7)();assert gpu.nf_source_packets_publish(publication)==0 and list(publication[:3])==[1,1,index];assert gpu.nf_source_packets_publish(publication)==1
  packet_stats=(C.c_uint*3)();assert gpu.nf_source_packets_stats(packet_stats)==0;nv,nd,overflow=packet_stats;assert nv>0 and nd>0 and overflow==0
  owned_vertices=C.create_string_buffer(nv*80);owned_offsets=(C.c_uint*(nd+1))();assert gpu.nf_source_packets_copy(owned_vertices,len(owned_vertices),owned_offsets,C.sizeof(owned_offsets))==0
  import struct,math
  assert all(math.isfinite(v[0]) for v in struct.iter_unpack('<d',owned_vertices.raw));assert owned_offsets[0]==0 and owned_offsets[-1]==nv and all((owned_offsets[j+1]-owned_offsets[j])%3==0 for j in range(nd))
  gpu.nf_source_texture_stats.argtypes=[C.c_void_p];gpu.nf_source_texture_copy.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t]
  ts=(C.c_uint*2)();assert gpu.nf_source_texture_stats(ts)==0;nt,nb=ts;assert nt>0 and nb>0
  tb=C.create_string_buffer(nb);tr=(C.c_uint*(nt*4))();di=(C.c_uint*nd)();assert gpu.nf_source_texture_copy(tb,nb,tr,C.sizeof(tr),di,C.sizeof(di))==0
  assert all(1<=x<=nt for x in di);assert all(tr[j*4+3]==tr[j*4]*tr[j*4+1]*4 and tr[j*4+2]+tr[j*4+3]<=nb for j in range(nt))
  gpu.nf_source_clip_copy.argtypes=[C.c_void_p,C.c_size_t];clips=(C.c_int*(nd*4))();assert gpu.nf_source_clip_copy(clips,C.sizeof(clips))==0
  assert all(0<=clips[j*4]<=clips[j*4+2]<=3840 and 0<=clips[j*4+1]<=clips[j*4+3]<=2160 for j in range(nd))
  gpu.nf_source_state_copy.argtypes=[C.c_void_p,C.c_size_t];states=C.create_string_buffer(nd*72);assert gpu.nf_source_state_copy(states,len(states))==0;Path(f'work/camera/prototype-runs/source-owned-state-{index}.bin').write_bytes(states.raw)
  gpu.nf_source_sky_info.argtypes=[C.c_void_p,C.c_void_p];gpu.nf_source_sky_copy.argtypes=[C.c_uint,C.c_void_p,C.c_size_t];sky_valid=(C.c_uint*2)();sky_weights=(C.c_double*2)();assert gpu.nf_source_sky_info(sky_valid,sky_weights)==0 and sky_valid[0]==1 and sky_weights[0]==1
  sky_hashes=[]
  for slot in range(2):
   if sky_valid[slot]:
    sky_bytes=C.create_string_buffer(153600);assert gpu.nf_source_sky_copy(slot,sky_bytes,len(sky_bytes))==0;sky_hashes.append(hashlib.sha256(sky_bytes.raw).hexdigest());Path(f'work/camera/prototype-runs/source-owned-sky-{index}-{slot}.rgba').write_bytes(sky_bytes.raw)
    assert 0<=sky_weights[slot]<=1
  gpu.nf_source_hud_planes_info.argtypes=[C.c_void_p];gpu.nf_source_hud_plane_copy.argtypes=[C.c_uint,C.c_void_p,C.c_size_t];hud_info=(C.c_uint*2)();assert gpu.nf_source_hud_planes_info(hud_info)==0 and hud_info[0]==1
  hud_hashes=[]
  for plane in range(3):
   hb=C.create_string_buffer(153600);assert gpu.nf_source_hud_plane_copy(plane,hb,len(hb))==0;hud_hashes.append(hashlib.sha256(hb.raw).hexdigest());Path(f'work/camera/prototype-runs/source-owned-hud-{index}-{plane}.rgba').write_bytes(hb.raw)
  count=gpu.nf_source_hud_batches_count();assert 0<count<=160;gpu.nf_source_hud_batches_copy.argtypes=[C.c_void_p,C.c_size_t];batch=C.create_string_buffer(count*112);assert gpu.nf_source_hud_batches_copy(batch,len(batch))==0;Path(f'work/camera/prototype-runs/source-owned-hud-batches-{index}.bin').write_bytes(batch.raw)
  packet_checks.append(dict(hud_batches=count,hud_batch_sha256=hashlib.sha256(batch.raw).hexdigest(),hud_info=list(hud_info),hud_hashes=hud_hashes,sky_valid=list(sky_valid),sky_weights=list(sky_weights),sky_hashes=sky_hashes,state_sha256=hashlib.sha256(states.raw).hexdigest(),clip_sha256=hashlib.sha256(bytes(clips)).hexdigest(),texture_count=nt,texture_bytes=nb,texture_sha256=hashlib.sha256(tb.raw).hexdigest(),frame=index,vertices=nv,draws=nd,overflow=overflow,sha256=hashlib.sha256(owned_vertices.raw).hexdigest()));Path(f'work/camera/prototype-runs/source-owned-vertices-{index}.bin').write_bytes(owned_vertices.raw)
  gpu.nf_source_backdrop_copy.argtypes=[C.c_void_p,C.c_size_t];backdrop=C.create_string_buffer(640)
  assert gpu.nf_source_backdrop_copy(backdrop,639)==1
  assert gpu.nf_source_backdrop_copy(backdrop,640)==0
  import concurrent.futures
  with concurrent.futures.ThreadPoolExecutor(1) as worker:assert worker.submit(gpu.nf_source_backdrop_copy,backdrop,640).result()==1
  assert gpu.nf_source_packets_reset()==1
  Path(f'work/camera/prototype-runs/source-owned-backdrop-{index}.rgba').write_bytes(backdrop.raw)
  packet_checks[-1]['backdrop_sha256']=hashlib.sha256(backdrop.raw).hexdigest();packet_checks[-1]['backdrop_copy_guards']=True
  from owned_source_d3d_present_consumer_candidate import OwnedD3DConsumer
  import numpy as np
  if consumer is None:consumer=OwnedD3DConsumer();consumer.bind_window()
  assert consumer.render(gpu,readback=False) is None
  present_results.append(consumer.present())
  native=consumer.render(gpu)
  import zlib
  ref=np.frombuffer(zlib.decompress(Path(f'work/camera/prototype-runs/gl-source-full-{index}.rgb.z').read_bytes()),np.uint8).reshape(2160,3840,3);packet_checks[-1]['d3d_different_pixels']=int(np.any(native!=ref,axis=2).sum());packet_checks[-1]['d3d_rgb_sha256']=hashlib.sha256(native.tobytes()).hexdigest()
  assert gpu.nf_source_packets_close()==0;assert gpu.nf_source_packets_begin(1,2,index)==0;assert gpu.nf_source_backdrop_copy(backdrop,640)==1

finally:
 if consumer is not None:consumer.close()
 assert gpu.nf_owned_gpu_close()
 if cached is not None:cached.close()
 if prepared is not None:prepared.close()
 history.close()
reference=json.loads(Path('work/camera/prototype-runs/source-direct-present-component.json').read_text());assert [x['d3d_rgb_sha256'] for x in packet_checks]==[x['d3d_rgb_sha256'] for x in reference['source_packet_checks']]
assert gpu.nf_owned_gpu_contexts()==0 and gpu.nf_owned_gpu_active_contexts()==0
result=dict(source_gl_contexts=0,result='PASS_CONTEXT_FREE_SOURCE_NATIVE_OUTPUT',source_packet_checks=packet_checks,direct_presentation_results=present_results,legacy_transfer_calls=0,source_framebuffer_readbacks=0,scope='Five source fixtures, persistent native D3D no-readback draw/present plus diagnostic D3D verification. No legacy bridge loaded or source framebuffer readback. GL source context/state/resources remain; all presents may be occluded, not live cadence proof.')
Path(sys.argv[2]).write_text(json.dumps(result,indent=2));print(result['result'],[x['status'] for x in present_results])

