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
from owned_native_source_recoverable_worker_candidate import NativeSourceWorker
session=None;results=[]
try:
 prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom);cached=PrecomputedSourceWorldSamples(prepared,tuple(x['alpha'] for x in expected),trace=True)
 boundaries=[]
 for scene in scenes:
  record=next(x for x in report['sky_capture_records'] if (x['epoch'],x['publication'])==scene.identity)
  origin=record['asset_origin'];offset=record['source']-0x08000000
  boundaries.append(SkyBoundary(record['epoch'],record['publication'],record['angle'],240,64,0,record['source'],origin,0x06002940,rom[offset:offset+15136]))
 origin=boundaries[0].asset_origin;asset=SkyAsset(origin,rom[origin-0x08000000:origin-0x08000000+15376])
 session=NativeSourceWorker()
 from owned_native_source_commit_adapter_candidate import NativeSourceCommitAdapter,P
 authority=C.CDLL(str(Path('work/camera/owned-draw-commit-candidate.dll').resolve()));authority.nf_owned_handoff_create.argtypes=[C.c_uint64];authority.nf_owned_handoff_create.restype=P;authority.nf_owned_handoff_pause.argtypes=[P,C.c_uint];authority.nf_owned_handoff_destroy.argtypes=[P]
 owner=authority.nf_owned_handoff_create(1);assert owner;adapter=NativeSourceCommitAdapter(session,owner);generation=1
 for index,item in enumerate(expected):
  alpha=item['alpha'];frame,camera,models,bounds,detail=cached.sample(alpha);offsets,mask,total,_=cached.source_masks[alpha]
  owned=OwnedSourceDraw(frame,camera,models,bounds,detail['geometry_records'],*cached.source_cameras,alpha,offsets,mask,total).attach_sky(asset.sample_continuous(*boundaries,alpha))
  hook=(lambda:authority.nf_owned_handoff_pause(owner,1)) if index==2 else None
  row=adapter.run(owned,1,generation,10,14,index,item['alpha'],0,diagnostic=True,on_prepared=hook)
  if index==2:
   assert row['native_result']==0 and row['presentation'] is None and row['commit']==[123]*8
   assert authority.nf_owned_handoff_pause(owner,0);generation=3
   row=adapter.run(owned,1,generation,10,14,index,item['alpha'],0,diagnostic=True)
  assert row['native_result']==-1 and row['presentation']['status']==3 and row['commit']==[123]*8
  row['native_rgb_sha256']=row['prepared']['native_rgb_sha256'];results.append(row)

finally:
 if 'owner' in globals():authority.nf_owned_handoff_destroy(owner)
 if session is not None:session.close();assert not session.thread.is_alive() and session.completed==12
 if cached is not None:cached.close()
 if prepared is not None:prepared.close()
 history.close()
reference=json.loads(Path('work/camera/prototype-runs/source-direct-present-component.json').read_text());assert [x['native_rgb_sha256'] for x in results]==[x['d3d_rgb_sha256'] for x in reference['source_packet_checks']]
r=dict(result='PASS_NATIVE_D3D_COMMIT_CANCELLATION_OCCLUSION',frames=results,scope='Five source fixture publications via native session; source GL contexts zero, native draw without readback then present; separate diagnostic readback validates hashes. No live game clock or visible cadence proof.')
Path(sys.argv[2]).write_text(json.dumps(r,indent=2));print(r['result'])
