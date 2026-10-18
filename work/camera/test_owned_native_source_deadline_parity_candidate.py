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
from owned_native_source_deadline_session_candidate import NativeSourceSession
session=None;results=[]
try:
 prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom);cached=PrecomputedSourceWorldSamples(prepared,tuple(x['alpha'] for x in expected),trace=True)
 boundaries=[]
 for scene in scenes:
  record=next(x for x in report['sky_capture_records'] if (x['epoch'],x['publication'])==scene.identity)
  origin=record['asset_origin'];offset=record['source']-0x08000000
  boundaries.append(SkyBoundary(record['epoch'],record['publication'],record['angle'],240,64,0,record['source'],origin,0x06002940,rom[offset:offset+15136]))
 origin=boundaries[0].asset_origin;asset=SkyAsset(origin,rom[origin-0x08000000:origin-0x08000000+15376])
 session=NativeSourceSession()
 session.commit_dll.nf_owned_handoff_create.argtypes=[C.c_uint64];session.commit_dll.nf_owned_handoff_create.restype=C.c_void_p
 session.commit_dll.nf_owned_handoff_destroy.argtypes=[C.c_void_p]
 owner=session.commit_dll.nf_owned_handoff_create(1);assert owner
 for index,item in enumerate(expected):
  alpha=item['alpha'];frame,camera,models,bounds,detail=cached.sample(alpha);offsets,mask,total,_=cached.source_masks[alpha]
  owned=OwnedSourceDraw(frame,camera,models,bounds,detail['geometry_records'],*cached.source_cameras,alpha,offsets,mask,total).attach_sky(asset.sample_continuous(*boundaries,alpha))
  row=session.prepare(owned,1,1,index)
  commit=session.present_at_deadline(owner,1,1,10,11,index,alpha,0)
  assert commit['native_result']==1 and commit['presentation']['status']==0
  row['native_commit']=commit
  rgb=C.create_string_buffer(3840*2160*4);assert session.consumer.d.nf_d3d_read(rgb,len(rgb))==0
  import numpy as np
  image=np.frombuffer(rgb.raw,np.uint8).reshape(2160,3840,4)[:,:,:3];row['native_rgb_sha256']=hashlib.sha256(image.tobytes()).hexdigest();results.append(row)

 d=session.consumer.d;bad=C.create_string_buffer(224);struct.pack_into('<4i',bad,96,0,0,3840,2160);struct.pack_into('<4i',bad,208,0,0,3840,2161)
 ids=(C.c_uint*4)(1010,1011,1004,1012);config=(C.c_float*8)(0,3840,2160,0,0,0,0,0);vertices=np.zeros((6,10),np.float32);before=(C.c_uint64*4)();after=(C.c_uint64*4)()
 assert d.nf_d3d_stats(before)==0
 assert d.nf_d3d_hud_batch(vertices.ctypes.data,6,ids,bad,2,224,config)==1
 assert d.nf_d3d_hud_batch(vertices.ctypes.data,6,ids,bad,2,223,config)==1
 assert d.nf_d3d_stats(after)==0 and list(before)==list(after),'Invalid tail drew prefix'

 world_vertices=np.zeros((12,10),np.float32);world_offsets=(C.c_uint*3)(0,6,12);world_ids=(C.c_uint*2)(0,0);world_states=C.create_string_buffer(144)
 for i in range(2):struct.pack_into('<8f8i2I',world_states,i*72,0,240,160,0,0,0,0,0,0,0,3840,2160,300,0,3240,2160,0,0)
 struct.pack_into('<I',world_states,136,4)
 assert d.nf_d3d_stats(before)==0
 assert d.nf_d3d_world_batch(world_vertices.ctypes.data,12,480,world_offsets,12,world_ids,8,world_states,2,144)==1
 assert d.nf_d3d_world_batch(world_vertices.ctypes.data,12,479,world_offsets,12,world_ids,8,world_states,2,144)==1
 assert d.nf_d3d_stats(after)==0 and list(before)==list(after),'Invalid world tail drew prefix'

finally:
 if session is not None:
  stats=(C.c_uint64*3)();assert session.consumer.d.nf_d3d_quad_cache_stats(stats)==0
  cache_before=list(stats);assert stats[1]>100 and 0<stats[2]<=8
  uploads=(C.c_uint64*2)();assert session.consumer.d.nf_d3d_world_upload_stats(uploads)==0 and list(uploads)==[5,0]
  session.commit_dll.nf_owned_handoff_destroy(owner)
  session.close();assert session.source.nf_owned_gpu_contexts()==0
  assert session.consumer.d.nf_d3d_quad_cache_stats(stats)==0 and stats[2]==0
  cache_after=list(stats)
 if cached is not None:cached.close()
 if prepared is not None:prepared.close()
 history.close()
reference=json.loads(Path('work/camera/prototype-runs/source-direct-present-component.json').read_text());assert [x['native_rgb_sha256'] for x in results]==[x['d3d_rgb_sha256'] for x in reference['source_packet_checks']]
r=dict(cache_before=cache_before,cache_after=cache_after,result='PASS_NATIVE_SOURCE_SESSION_BOUNDARY',frames=results,scope='Five source fixture publications via actual owner-thread native deadline commit; source GL contexts zero, native draw without readback then present; separate diagnostic readback validates hashes. No live game clock or visible cadence proof.')
Path(sys.argv[2]).write_text(json.dumps(r,indent=2));print(r['result'])
